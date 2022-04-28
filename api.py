from flask import Flask, request
from flask_cors import CORS
from canvasapi import Canvas

app = Flask(__name__)
CORS(app)

@app.route('/canvas/get_assignments/<domain>/<user_token>/<course_id>')
def get_assignments(domain, user_token, course_id):
    canvas = Canvas("https://" +  domain, user_token)
    assignments = canvas.get_course(int(course_id)).get_assignments()
    out = []
    for ass in assignments:
        out.append({'name': ass.__getattribute__('name'), 'due': ass.__getattribute__('due_at')})
    return {'assignments' : out}

# method to read Canvas Classes
# update notion function