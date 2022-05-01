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


@app.route('/run/<domain>/<course_id>/<course>/<db_id>')
def run(domain, course_id, course, db_id):
    """api endpoint that acts as a wrapper for all sub functions, and basic error handling"""
    new_ = get_assignments(domain, course_id)['assignments']
    if (type(new_)) == str():
        return new_
    curr_ = read_notion(db_id)
    if (type(curr_)) == str():
        return curr_
    update_ = update_notion(db_id, new_, curr_, course)
    if (type(update_)) == str():
        return update_
    return 'success'

def get_assignments(domain, course_id):
    try:
        """query the canvas api and return the current assignments as a dictionary"""
        user_token = os.getenv('CANVAS')
        canvas = Canvas("https://" + domain, user_token)
        assignments = canvas.get_course(int(course_id)).get_assignments()
        out = []

        for ass in assignments:
            out.append({'name': ass.__getattribute__('name'),
                    'due': str(ass.__getattribute__('due_at'))[:10]})
        return {'assignments': out}
    except Exception as e:
        return str(e)

def read_notion(db_id):
    """this function reads notion and returns the current state as a dictionary with only the relevant details"""
    
    try:
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
    except Exception as e:
        return str(e)

def update_notion(db_id, new_, curr_, course):
    """intelligently updates notion so that we do not have duplicate data"""
    try:
        for ass in new_:
            if ass['name'] in curr_.keys():
                payload = {'properties': {'Due':{'start':ass['due']}}}
                requests.patch(
                    'https://api.notion.com/v1/pages/'+curr_['name']['id'], headers=headers, json=payload)
            else:
                if (curr_[ass['name']]['date'] != ass['date']):
                    payload={'parent' : {'database_id':db_id}, 
                            'properties': {'Assignment Name' :{'title' : [{'text':{'content' : ass['name']}}]}, 
                                                                'Due' : {'date':{'start':ass['due']}}, 
                                                                'Course' : {'select' : {'name' : course}}}}
                    requests.post("https://api.notion.com/v1/pages", headers=headers,json=payload)
        return True
    except Exception as e:
        return str(e)
    