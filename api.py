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
headers = {'Authorization': os.getenv(
    'NOTION'), 'Notion-Version': '2021-08-16'}


@app.route('/run/<domain>/<canvas_token>/<course_id>/<course_name>/<db_id>')
def run(domain, canvas_token, course_id, course_name, db_id):
    """api endpoint that acts as a wrapper for all sub functions, and basic error handling"""
    try:
        new_state = get_assignments(domain, canvas_token, course_id)['assignments']
        curr_state = read_notion(db_id)
        update_notion(db_id, new_state, curr_state, course_name)
        return 'You are now up to date!'
    except Exception as e:
        return str(e).capitalize()
        
def get_assignments(domain,canvas_token, course_id):
    try:
        """query the canvas api and return the current assignments as a dictionary"""

        canvas = Canvas("https://" + domain, canvas_token)
        assignments = canvas.get_course(int(course_id)).get_assignments()
        out = []

        for ass in assignments:
            out.append({'name': ass.__getattribute__('name'),
                        'due': str(ass.__getattribute__('due_at'))[:10]})
        return {'assignments': out}
    except Exception as e:
        ex = str(type(e))
        
        # logging to console
        print(type(e), e)

        if ('Unauthorized' in ex):
            message = "You do not have access to this class in Canvas"
        elif ('InvalidAccessToken' in ex):
            message = "You passed in an invalid access token"
        else:
            # Unhandled exception
            print('Unhandled Canvas exception: ' + str(e))
            message = "Unhandled Exception"

        raise Exception(message)

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

        if (res.status_code != 200):
            notion_errors(json.loads(res._content)['code'])

        res_json = res.json()
        all_tasks.extend(res_json['results'])
       
        has_more = res_json['has_more']
        start_cursor = res_json['next_cursor']
    temp = {}
    for task in all_tasks:
        date=''
        if (task['properties']['Due']['date'] == None):
            date = 'None'
        else :
            date = task['properties']['Due']['date']['start']
        temp[task['properties']['Assignment Name']['title'][0]['text']['content']] = {
            'id': task['id'], 
            'due': task['properties']['Due']['date'] == date
            }
    return temp

def notion_errors(code):
    """returns readable strings for any Notion errors."""

    errors = {"unauthorized" : "The api token in backend is not working. Contact Abhi for a fix",
                 "restricted_resource": "You have not shared the table with Abhi.",
                 "object_not_found" : "You have passed in an invalid database url",
                 "database_connection_unavailable" : "Notion API is unqueryable right now"}

    try:
        message = errors[code]
        raise Exception(message)
    except:
        print(code)
        raise Exception('Unhandled Notion Exception')

    pass

def update_notion(db_id, new_state, curr_state, course_name):
    """intelligently updates notion so that we do not have duplicate data"""
    # equality checking, equality checking to prevent unnecessary calls, missing column issue, 
    # better error handling (for any unknown errors its hard to pinpoint cause because of current rendering)
    for assignment in new_state:
        payload = {'parent': {'database_id': db_id},
                   'properties': {'Assignment Name': {'title': [{'text': {'content': assignment['name']}}]},
                                                      'Due': {'date': {'start': assignment['due']}},
                                                      'Course': {'select': {'name': course_name}}}}
        if (assignment['due'] == 'None'):
            del payload['properties']['Due']
        res=''
        if assignment['name'] in curr_state.keys():
            res = requests.patch(
                    'https://api.notion.com/v1/pages/'+curr_state[assignment['name']]['id'], headers=headers, json=payload)
        else:  
            res = requests.post("https://api.notion.com/v1/pages",headers=headers, json=payload)
        if (res.status_code != 200):
            notion_errors(json.loads(res._content)['code'])
    
