import json
import time
import validators

from flask import Flask, jsonify, request, make_response, Response
from flask_cors import CORS, cross_origin
from src.app import App

flask_app = Flask(__name__)
CORS(flask_app)

app = App()

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
        res = make_response('A repository with the given name already exists.', 400)
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
    except:
        res = make_response("There's something wrong, please check again.", 400)
    return res

@flask_app.route('/repository/<repo_name>/scraper/file/submit/', methods=['POST'])
def submit_file(repo_name):
    try:
        repo = app.get_repo(name=repo_name)
        f = request.files['file'].read().decode('utf-8')
        start_urls = f.split('\n')
        repo.submit_file(start_urls)
        res = jsonify({"row_"+str(index): item for index,item in enumerate(start_urls[:5])})
    except: 
        res = make_response("Given unsupported file format.", 400)
    return res

@flask_app.route('/repository/<repo_name>/scraper/file/confirm/')
def scrape_file(repo_name):
    try:
        repo = app.get_repo(name=repo_name)
        repo.start_scrape()
        res = make_response('OK.', 200)
    except:
        res = make_response("Something's wrong.", 400)
    return res

@flask_app.route('/repository/<repo_name>/scraper/file/discard/')
def discard_file(repo_name):
    try:
        repo = app.get_repo(name=repo_name)
        repo.discard_file()
        res = make_response("File is discarded.", 200)        
    except:
        res = make_response("File could not be discarded.", 400)
    return res

@flask_app.route('/repository/stream/<repo_name>', methods=['GET'])
def repo_status(repo_name):
    def response(repo):
        while True:
            r = repo.get_status()
            status = {
                'name': r['name'], 
                'bubble':{
                    'scraper':{
                        'scraped_file_count':   r['bubble']['scraper']['scraped_file_count'],
                        'total_file_count'  :   r['bubble']['scraper']['total_file_count'],
                        'state'             :   r['bubble']['scraper']['state'] 
                    }
                }
            }
            status = json.dumps(status)
            time.sleep(0.1)
            yield 'data: {}\n\n'.format(status)
    
    r = app.get_repo(name=repo_name)

    return Response(response(r), mimetype='text/event-stream')

@flask_app.route('/repository/<repo_name>/graph/', methods=['GET'])
def get_graph(repo_name):
    repo = app.get_repo(name=repo_name)
    parser = repo.parser
    graph = parser.graph
    res = graph.create_response()
    return jsonify(res)

@flask_app.route('/repository/<repo_name>/graph/expand/', methods=['POST'])
def expand_graph(repo_name):
    repo = app.get_repo(name=repo_name)
    parser = repo.parser
    #graph = parser.graph
    node_id = request.json['node_id']
    #graph.expand_node(int(node_id))
    parser.expand_node(node_id)
    res = parser.graph.create_response()
    return jsonify(res)

@flask_app.route('/repository/<repo_name>/graph/delete/', methods=['POST'])
def del_node(repo_name):
    repo = app.get_repo(name=repo_name)
    parser = repo.parser
    #graph = parser.graph
    node_id = request.json['node_id']
    #graph.del_node(int(node_id))
    parser.del_node(node_id)
    res = parser.graph.create_response()
    return jsonify(res)

@flask_app.route('/repository/<repo_name>/datatable/add/', methods=['POST'])
def add_column(repo_name):
    repo = app.get_repo(name=repo_name)
    parser = repo.parser
    column_name = request.json['column_name']
    node_id       = request.json['node_id']
    parser.add_column(column_name, node_id)
    res = make_response('OK.', 200)
    return res

@flask_app.route('/repository/<repo_name>/datatable/delete/', methods=['POST'])
def del_column(repo_name):
    repo = app.get_repo(name=repo_name)
    parser = repo.parser
    column_name = request.json['column_name'] 
    parser.del_column(column_name)
    res = make_response('OK.', 200)
    return res

@flask_app.route('/repository/<repo_name>/datatable/clear/', methods=['POST'])
def clear_datatable(repo_name):
    repo = app.get_repo(name=repo_name)
    parser = repo.parser
    parser.datatable.clear_datatable()
    res = make_response('OK.', 200)
    return res