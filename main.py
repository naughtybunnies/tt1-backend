import json
import time

from flask import Flask, jsonify, request, make_response, Response
from urllib3.exceptions import URLRequired

from flask_cors import CORS, cross_origin
from src.app import App

flask_app = Flask(__name__)
CORS(flask_app)

app = App()

@flask_app.route('/', methods=['GET'])
def index():
    return 'TT1 Senior Project'
    
@flask_app.route('/getstatus', methods=['GET'])
def getstatus():
    repo_status = [repo.get_status() for repo in app.repo]
    return jsonify(repo_status)

@flask_app.route('/repository/', methods=['POST'])
def create_repo():
    try:
        repo_name = request.json['name']
        app.create_repo(repo_name)
        res = make_response('New repository created.', 203)
    except:
        res = make_response('A repository with this name already exists.', 400)
    return res
    
@flask_app.route('/repository/delete/', methods=['POST'])
def delete_repo():
    try:
        repo_name = request.json['name']
        repo = app.get_repo(name=repo_name)
        app.delete_repo(repo)
        res = make_response('The repository was deleted.', 200)
    except:
        res = make_response('Could not delete the repository.', 400)
    return res

@flask_app.route('/repository/rename/', methods=['POST'])
def rename_repo():
    try:
        repo_name = request.json['name']
        new_name  = request.json['new_name']
        repo = app.get_repo(name=repo_name) 
        app.rename_repo(repo, new_name)
        res = make_response('The repository was renamed.', 200)
    except:
        res = make_response('Could not rename the repository.', 400)
    return res

@flask_app.route('/repository/scraper/seturl/', methods=['POST'])
def set_url():
    try:
        repo_name = request.json['reponame']
        url       = request.json['baseurl']
        start_key = request.json['start']
        end_key   = request.json['end']
        repo = app.get_repo(name=repo_name)
        app.set_url(repo, url, start_key, end_key)
        res = make_response('OK.', 200)
    except URLRequired:
        res = make_response("Base url is needed.", 400)
    return res