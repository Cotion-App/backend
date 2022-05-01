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
def run(domain, course_id, db_id, course):
    new_ = get_assignments(domain, course_id)['assignments']
    curr_ = read_notion(db_id)
    for ass in new_:
        if ass['name'] in curr_.keys():
            payload = {'properties': {'Due':{'start':ass['due']}}}
            requests.patch(
                'https://api.notion.com/v1/pages/'+curr_['name']['id'], headers=headers, json=payload)
        else:
            payload={'parent' : {'database_id':'e8f06f32275c45a48dcbe56ec9250aed'}, 
                     'properties': {'Assignment Name' :{'title' : [{'text':{'content' : ass['name']}}]}, 
                                                        'Due' : {'date':{'start':ass['due']}}, 
                                                        'Course' : {'select' : {'name' : course}}}}
            requests.post("https://api.notion.com/v1/pages", headers=headers,json=payload)
    return ''

def get_assignments(domain, course_id):
    user_token = os.getenv('CANVAS')
    canvas = Canvas("https://" + domain, user_token)
    assignments = canvas.get_course(int(course_id)).get_assignments()
    out = []

    for ass in assignments:
        out.append({'name': ass.__getattribute__('name'),
                   'due': str(ass.__getattribute__('due_at'))[:10]})
    return {'assignments': out}


def read_notion(db_id):
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

# @app.route('/notion/update')
# def update_notion():

#     pass
# update notion function
