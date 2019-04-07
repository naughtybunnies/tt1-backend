import json
import time

from flask import Flask, jsonify, request, make_response, send_file, Response
from flask_cors import CORS, cross_origin
from src.app import App

flask_app = Flask(__name__)
CORS(flask_app)

app = App()


@flask_app.route('/getstatus', methods=['GET'])
def getstatus():
    '''Get repositories status API. [ Repository REST API ] [ GET ]

    Return information of repositories. Information includes scraper, parser, and exporter status.
    '''
    repo_status = [repo.get_status() for repo in app.repo]
    return jsonify(repo_status)


@flask_app.route('/repository/', methods=['POST'])
def create_repo():
    '''Create repository API. [ Repository REST API ] [ POST ]

    Request:
        { "name": "" }

    Reponse:
        203 - Successful create
        400 - Error - Duplicating name
    '''
    try:
        repo_name = request.json['name']
        app.create_repo(repo_name)
        res = make_response('New repository created.', 203)
    except:
        res = make_response(
            'A repository with the given name already exists.', 400)
    return res


@flask_app.route('/repository/delete/', methods=['POST'])
def delete_repo():
    '''Delete repository API. [ Repository REST API ] [ POST ]

    Request:
        { "name": "" }

    Response:
        200 - Successful delete
        400 - Error deleting
    '''
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
    '''Rename repository API. [ Repository REST API ] [ POST ]

    Request:
        { "name": ",
          "new_name: "" }

    Response:
        200 - Successful rename
        400 - Error renaming
    '''
    try:
        repo_name = request.json['name']
        new_name = request.json['new_name']
        repo = app.get_repo(name=repo_name)
        app.rename_repo(repo, new_name)
        res = make_response('The repository was renamed.', 200)
    except:
        res = make_response('Could not rename the repository.', 400)
    return res


@flask_app.route('/repository/scraper/seturl/', methods=['POST'])
def set_url():
    '''Set url for scraper. [ Scraper REST API ] [ POST ]

    Request:
        { 
            "reponame": "",
            "baseurl": "",
            "start": "",
            "end": "" 
        }

    Response:
        200 - Successful set url and scrapes
        400 - Error scraping
    '''
    try:
        repo_name = request.json['reponame']
        url = request.json['baseurl']
        start_key = request.json['start']
        end_key = request.json['end']
        repo = app.get_repo(name=repo_name)

        # set url and start scraping immediately
        app.set_url(repo, url, start_key, end_key)

        res = make_response('OK.', 200)
    except:
        res = make_response(
            "There's something wrong, please check again.", 400)
    return res


@flask_app.route('/repository/<repo_name>/scraper/file/submit/', methods=['POST'])
def submit_file(repo_name):
    '''Set url for scraper using file upload. [ Scraper REST API ] [ POST ]

    Request:
        file

    Response:
        200 - { sample urls }
        400 - Error file format
    '''
    try:
        repo = app.get_repo(name=repo_name)
        f = request.files['file'].read().decode('utf-8')
        start_urls = f.split('\n')
        repo.submit_file(start_urls)
        res = jsonify({"row_"+str(index): item for index,
                       item in enumerate(start_urls[:5])})
    except:
        res = make_response("Given unsupported file format.", 400)
    return res


@flask_app.route('/repository/<repo_name>/scraper/file/confirm/')
def scrape_file(repo_name):
    '''Start file scraping. [ Scraper REST API ] [ GET ]

    Response:
        200 - Successful scrapes using file
        400 - Error scraping
    '''
    try:
        repo = app.get_repo(name=repo_name)
        repo.start_scrape()
        res = make_response('OK.', 200)
    except:
        res = make_response("Something's wrong.", 400)
    return res


@flask_app.route('/repository/<repo_name>/scraper/file/discard/')
def discard_file(repo_name):
    '''Remove file to scrape. [ Scraper REST API ] [ GET ]

    Response:
        200 - Successful remove file
        400 - Error removing file
    '''
    try:
        repo = app.get_repo(name=repo_name)
        repo.discard_file()
        res = make_response("File is discarded.", 200)
    except:
        res = make_response("File could not be discarded.", 400)
    return res


@flask_app.route('/repository/stream/<repo_name>', methods=['GET'])
def repo_status(repo_name):
    '''Web socket streaming scraping status. [ Scraper REST API ] [ GET ]

    Response:
        200 - { "name" : "repository name",
                "bubble": {
                    "scraper": {
                        "scraped_file_count": "",
                        "total_file_count": "",
                        "state": ""
                    }
                }
            }
    '''
    def response(repo):
        while True:
            r = repo.get_status()
            status = {
                'name': r['name'],
                'bubble': {
                    'scraper': {
                        'scraped_file_count':   r['bubble']['scraper']['scraped_file_count'],
                        'total_file_count':   r['bubble']['scraper']['total_file_count'],
                        'state':   r['bubble']['scraper']['state']
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
    '''Retrieve graph of the repository. [ Parser REST API ] [ GET ]

    Response:
        200 - Graph response - { "nodes" : [ {"title": "", "id": "", "label": ""} ] }
    '''
    repo = app.get_repo(name=repo_name)
    parser = repo.parser
    graph = parser.create_graph()
    res = graph.create_response()
    return jsonify(res)


@flask_app.route('/repository/<repo_name>/graph/expand/', methods=['POST'])
def expand_graph(repo_name):
    '''Expand tree from selected node. [ Parser REST API ] [ POST ]

    Request:
        { "node_id": "" }

    Response:
        200 - Graph response - { "nodes" : [ {"title": "", "id": "", "label": ""} ] }
    '''
    repo = app.get_repo(name=repo_name)
    parser = repo.parser
    #graph = parser.graph
    node_id = request.json['node_id']
    # graph.expand_node(int(node_id))
    parser.expand_node(node_id)
    res = parser.graph.create_response()
    return jsonify(res)


@flask_app.route('/repository/<repo_name>/graph/delete/', methods=['POST'])
def del_node(repo_name):
    '''Delete selected node from tree. [ Parser REST API ] [ POST ]

    Request:
        { "node_id": "" }

    Response:
        200 - Graph response - { "nodes" : [ {"title": "", "id": "", "label": ""} ] }
    '''
    repo = app.get_repo(name=repo_name)
    parser = repo.parser
    #graph = parser.graph
    node_id = request.json['node_id']
    # graph.del_node(int(node_id))
    parser.del_node(node_id)
    res = parser.graph.create_response()
    return jsonify(res)


@flask_app.route('/repository/<repo_name>/datatable/', methods=['GET'])
def get_datatable(repo_name):
    '''Get repository data table. [ Parser REST API ] [ GET ]

    Response:
        200 - Data Table - [ { "id": "" }, ... ]
    '''
    repo = app.get_repo(name=repo_name)
    parser = repo.parser
    res = parser.datatable.create_response(repo.get_id())
    return jsonify(res)


@flask_app.route('/repository/<repo_name>/datatable/add/', methods=['POST'])
def add_column(repo_name):
    '''Create new column in repository data table. [ Parser REST API ] [ POST ]

    Request:
        { "column_name": "",
          "node_id": "" 
        }

    Response:
        200 - Data Table - [ { "id": "" }, ... ]
    '''
    repo = app.get_repo(name=repo_name)
    parser = repo.parser
    column_name = request.json['column_name']
    node_id = request.json['node_id']
    parser.add_column(column_name, node_id)
    res = parser.datatable.create_response(repo.get_id())
    return jsonify(res)


@flask_app.route('/repository/<repo_name>/datatable/delete/', methods=['POST'])
def del_column(repo_name):
    '''Delete column from repository data table. [ Parser REST API ] [ POST ]

    Request:
        { "column_name": "" }

    Response:
        200 - Data Table - [ { "id": "" }, ... ]
    '''
    repo = app.get_repo(name=repo_name)
    parser = repo.parser
    column_name = request.json['column_name']
    parser.del_column(column_name)
    res = parser.datatable.create_response(repo.get_id())
    return jsonify(res)


@flask_app.route('/repository/<repo_name>/datatable/clear/', methods=['POST'])
def clear_datatable(repo_name):
    '''Clear repository data table. [ Parser REST API ] [ POST ]

    Request:
        { }

    Response:
        200 - Data Table - [ { "id": "" }, ... ]
    '''
    repo = app.get_repo(name=repo_name)
    parser = repo.parser
    parser.datatable.clear_datatable()
    res = parser.datatable.create_response(repo.get_id())
    return jsonify(res)


@flask_app.route('/repository/<repo_name>/exporter/json', methods=['GET'])
def export_json(repo_name):
    '''Export data table into JSON file [ Export REST API ] [ GET ]

    Response:
        200 - JSON File
    '''
    repo = app.get_repo(name=repo_name)
    res = repo.start_export()
    content = json.dumps(res, ensure_ascii=False)
    return Response(content,
                    mimetype='application/json',
                    headers={'Content-Disposition': 'attachment;filename={}.json'.format(repo.get_name())})
    #path = repo.exporter.get_parsed_path()
    # return send_file(path)
    #res = repo.start_export()
    # return jsonify(res)