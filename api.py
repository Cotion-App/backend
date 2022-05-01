from flask import Flask
import requests
from flask_cors import CORS
from canvasapi import Canvas
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)
load_dotenv()
headers = {'Authorization': os.getenv(
    'NOTION'), 'Notion-Version': '2021-08-16'}


@app.route('/run/<domain>/<canvas_token>/<course_id>/<course_name>/<db_id>')
def run(domain, canvas_token, course_id, course_name, db_id):
    """api endpoint that acts as a wrapper for all sub functions, and basic error handling"""
    try:
        new_state = get_assignments(domain, canvas_token, course_id)['assignments']
        curr_state = read_notion(db_id)
        update_notion(db_id, new_state, curr_state, course_name)
        return 'success'
    except Exception as e:
        return str(e)


def get_assignments(domain,canvas_token, course_id):
    """query the canvas api and return the current assignments as a dictionary"""

    canvas = Canvas("https://" + domain, canvas_token)
    assignments = canvas.get_course(int(course_id)).get_assignments()
    out = []

    for ass in assignments:
        out.append({'name': ass.__getattribute__('name'),
                    'due': str(ass.__getattribute__('due_at'))[:10]})
    return {'assignments': out}


def read_notion(db_id):
    """this function reads notion and returns the current state as a dictionary with only the relevant details"""

    has_more = True
    start_cursor = None

    all_tasks = []

    while has_more:
        if start_cursor:
            res = requests.post('https://api.notion.com/v1/databases/' + db_id +
                                '/query', headers=headers, json={'start_cursor': start_cursor})
        else:
            res = requests.post(
                'https://api.notion.com/v1/databases/' + db_id + '/query', headers=headers)
        res_json = res.json()
        all_tasks.extend(res_json['results'])
        has_more = res_json['has_more']
        start_cursor = res_json['next_cursor']
    temp = {}
    for task in all_tasks:
        temp[task['properties']['Assignment Name']['title'][0]['text']['content']] = {
            'id': task['id'], 'due': task['properties']['Due']['date']['start']}
    return temp


def update_notion(db_id, new_state, curr_state, course_name):
    """intelligently updates notion so that we do not have duplicate data"""

    for ass in new_state:
        if ass['name'] in curr_state.keys():
            payload = {'properties': {'Due': {'start': ass['due']}}}
            requests.patch(
                'https://api.notion.com/v1/pages/'+curr_state['name']['id'], headers=headers, json=payload)
        else:
            if (curr_state[ass['name']]['date'] != ass['date']):
                payload = {'parent': {'database_id': db_id},
                           'properties': {'Assignment Name': {'title': [{'text': {'content': ass['name']}}]},
                                          'Due': {'date': {'start': ass['due']}},
                                          'Course': {'select': {'name': course_name}}}}
                requests.post("https://api.notion.com/v1/pages",
                              headers=headers, json=payload)
