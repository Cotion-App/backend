from flask import Flask
import requests
from flask_cors import CORS
from canvasapi import Canvas
import os
from dotenv import load_dotenv
import json

app = Flask(__name__)
CORS(app)
load_dotenv()


@app.route('/notion/<temp_code>/<redirect_uri>')
def notion_auth(temp_code, redirect_uri):
    """exchanges a one time use code for a user's auth token"""
    auth = {'Authorization': "Basic " +
            os.getenv('AUTH'), 'Content-Type': 'application/json'}
    payload = {'grant_type': 'authorization_code',
               'code': temp_code, 'redirect_uri': "https://"+redirect_uri}
    res = requests.post(
        'https://api.notion.com/v1/oauth/token', headers=auth, json=payload)
    try:
        if res.status_code != 200:
            notion_errors(json.loads(res._content))
        return res.json()['access_token'], 200
    except Exception as e:
        return str(e).capitalize(), 401


@app.route('/run/<domain>/<canvas_token>/<course_id>/<course_name>/<db_id>/<notion_token>')
def run(domain, canvas_token, course_id, course_name, db_id, notion_token):
    """api endpoint that acts as a wrapper for all sub functions, and basic error handling"""
    try:
        new_state = get_assignments(domain, canvas_token, course_id)
        headers = {'Authorization': notion_token,
                   'Notion-Version': '2021-08-16'}
        curr_state = read_notion(db_id, headers)
        update_notion(db_id, new_state, curr_state, course_name, headers)
        return 'You are now up to date!', 200
    except Exception as e:
        return str(e).capitalize()


def get_assignments(domain, canvas_token, course_id):

    try:
        """query the canvas api and return the current assignments as a dictionary"""

        canvas = Canvas("https://" + domain, canvas_token)
        assignments = canvas.get_course(int(course_id)).get_assignments()
        out = []

        for ass in assignments:
            out.append({'name': ass.__getattribute__('name'),
                       'due': str(ass.__getattribute__('due_at'))[:10]})
        return out
    except Exception as e:
        ex = str(type(e))

        if "Unauthorized" in ex:
            message = "Unauthorized Class Access"
        elif "InvalidAccessToken" in ex:
            message = "Invalid Canvas Token"
        else:
            print(e.__class__, str(e), e.__traceback__)
            message = "Unknown Error, Try Again Later"

        raise Exception(message)


def read_notion(db_id, headers):
    """reads notion and returns the current state as a dictionary with only the relevant details"""
    has_more = True
    start_cursor = None
    all_entries = []

    while has_more:
        if start_cursor:
            res = requests.post('https://api.notion.com/v1/databases/' + db_id +
                                '/query', headers=headers, json={'start_cursor': start_cursor})
        else:
            res = requests.post(
                'https://api.notion.com/v1/databases/' + db_id + '/query', headers=headers)
        if (res.status_code != 200):
            notion_errors(json.loads(res._content)['code'])

        res_json = res.json()
        all_entries.extend(res_json['results'])

        has_more = res_json['has_more']
        start_cursor = res_json['next_cursor']
    temp = {}
    i = 0

    for entry in all_entries:
        if i == 0:
            needed_cols = ['Course', 'Due', 'Assignment Name']
            for col in needed_cols:
                if col not in entry['properties'].keys():
                    raise Exception('You are missing ' + col + ' column.')
            i += 1
        date = "None" if entry['properties']['Due']['date'] == None else entry['properties']['Due']['date']['start']
        course = "None" if entry['properties']['Course']['select'] == None else entry['properties']['Course']['select']['name']
        if len(entry['properties']['Assignment Name']['title']) > 0:
            temp[entry['properties']['Assignment Name']['title'][0]['text']['content']] = {
                'id': entry['id'],
                'due': date,
                'course': course
            }

    return temp


def notion_errors(code):
    """returns custom strings for all Notion errors."""
    errors = {"invalid_grant": "Invalid grant",
              "unauthorized": "invalid auth token",
              "restricted_resource": "restricted access",
              "object_not_found": "Forgot to share with Cotion", }

    try:
        message = errors[code]
        raise Exception(message)
    except Exception as e:
        print(code, e.__class__, str(e), e.__traceback__)
        raise Exception('Try again later.')


def update_notion(db_id, new_state, curr_state, course_name, headers):
    """intelligently updates notion so that we do not have duplicate data"""

    for assignment in new_state:
        payload = {'parent': {'database_id': db_id},
                   'properties': {'Assignment Name': {'title': [{'text': {'content': assignment['name']}}]},
                                  'Due': {'date': {'start': assignment['due']}},
                                  'Course': {'select': {'name': course_name}}}}
        if (assignment['due'] == 'None'):
            del payload['properties']['Due']
        if assignment['name'] in curr_state.keys() and course_name == curr_state[assignment['name']]['course'] and assignment['due'] == curr_state[assignment['name']]['due']:
            pass
        else:
            if assignment['name'] in curr_state.keys() and course_name == curr_state[assignment['name']]['course']:
                res = requests.patch(
                    'https://api.notion.com/v1/pages/'+curr_state[assignment['name']]['id'], headers=headers, json=payload)
            else:
                res = requests.post(
                    "https://api.notion.com/v1/pages", headers=headers, json=payload)

            if res.status_code != 200:
                notion_errors(json.loads(res._content)['code'])
