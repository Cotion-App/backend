from flask import Flask, request
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

@app.route('/users/<id>/phone/<phone>')
def add_phone(id, phone):
    """
    Add your phone number to the coursify database

    Returns:
        user_phone (string): the number that was added to the database
    """
    return phone