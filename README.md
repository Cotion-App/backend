# Cotion Backend
 > A Flask Server that handles the API requests for Cotion Frontend
 
 ## Overview
 The backend server is built using [Python](https://www.python.org) and [Flask](https://flask.palletsprojects.com/en/2.1.x/) and handles any API behavior. This server is used to retrieve courses from Canvas, read the current set of assignments in Notion, update the assignments in Notion, and also generate temporary authorization tokens for Cotion to use. This server is currently being hosted on Heroku.
 
 ## Running Locally
 
 I still need to reformat the code so it allows others to run the code locally. Currently, my Flask server is setup to run based off a [public integration](https://www.notion.so/help/create-integrations-with-the-notion-api) setup. Running the code locally means you probably want to setup the server to run as a private integration. That being said, here's how to run the server locally.
 
 ### Requisite Software
 - Python 3.6 or higher
 
 ### Running the Server
 After cloning the repo to your local machine run the following lines of code
 
 ```
 source venv/bin/activate
 flask run
 ```
 
 The server should be up and running at `127.0.0.1:5000`
 
 

 
