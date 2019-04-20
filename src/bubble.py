from multiprocessing import Process, Manager, Value
from urllib import parse
from src.config import PATH_REPO, PATH_SCRAPED, PATH_PARSED
from src.graph import Graph, Node
from src.datatable import DataTable
from src.rdf    import RDF_API
from bs4 import BeautifulSoup

import requests
import os
import re
import time
import pickle
import sys
import re
import json


class Bubble(object):
    state = 'Unavailable'
    name = 'Bubble'
    repo = None

    def __init__(self, repo, data=None):
        if data == None:
            self.set_state('Unavailable')
        else:
            self.__dict__ = data
        self.set_repo(repo)

    def get_bubble(self):
        return {
            'state': self.get_state()
        }

    def get_state(self):
        return self.state

    def get_repo(self):
        return self.repo

    def set_state(self, state):
        self.state = state

    def set_repo(self, repo):
        self.repo = repo


class Scraper(Bubble):

    process = None

    def __init__(self, repo, data=None):
        if data == None:  # Crate a new scraper when a new repo is created
            data = {
                'state'             : 'Ready',
                'scraped_file_count': 0,
                'total_file_count'  : 0,
                'start_urls'        : []
            }
        super().__init__(repo, data)
        self.name = 'Scraper'

    def get_bubble(self):
        return {
            'state'             : self.get_state(),
            'scraped_file_count': self.get_scraped_file_count(),
            'total_file_count'  : self.get_total_file_count(),
            'start_urls'        : self.get_start_urls()
        }

    def get_scraped_file_count(self):
        path_scraped = os.path.join(
            PATH_REPO, self.repo.get_id(), PATH_SCRAPED)
        scraped_file = os.listdir(path_scraped)
        return len(scraped_file)

    def get_total_file_count(self):
        return self.total_file_count

    def get_start_urls(self):
        return self.start_urls

    def set_url(self, url, start_key, end_key):
        '''
        split = parse.urlsplit(url)
        query  = [re.sub('[{}]','',q) for q in split.query.split(',')]
        self.start_urls = [
            {
                'url':re.sub('[{][a-z]*[}]','{}={}'.format(query[0],key),url),
                'key': key
            } for key in range(int(start_key), int(end_key)+1)
        ]
        '''
        self.start_urls = [
            {
                'url': url.format(key),
                'key': key
            } for key in range(int(start_key), int(end_key)+1)
        ]
        self.total_file_count = len(self.start_urls)
        self.start_scrape()

    def submit_file(self, start_urls):
        self.start_urls = [
            {
                'url': url,
                'key': index
            } for index, url in enumerate(start_urls)
        ]
        self.total_file_count = len(self.start_urls)

    def discard_file(self):
        self.start_urls = []
        self.total_file_count = 0
        self.clear()

    def set_file(self, start_urls):
        self.start_urls = [
            {
                'url': url,
                'key': index
            } for index, url in enumerate(start_urls)
        ]
        self.total_file_count = len(self.start_urls)
        self.start_scrape()

    def clear(self):
        self.scraped_file_count = 0
        path = os.path.join(PATH_REPO, self.repo.get_id(), PATH_SCRAPED)
        files = os.listdir(path)
        for f in files:
            path_file = os.path.join(path, f)
            # print(path_file)
            os.remove(path_file)

    def start_scrape(self):
        def scrape(repo, start_urls):
            with requests.Session() as s:
                for url in start_urls:
                    res = s.get(url['url'])
                    print('{} {}'.format(res.url, res.status_code))
                    res.encoding = 'utf-8'
                    save_file(repo, res, url['key'])

        def save_file(repo, res, key):
            path_scraped = os.path.join(PATH_REPO, repo, PATH_SCRAPED)
            path_file = os.path.join(path_scraped, str(key)+'.html')
            with open(path_file, 'w') as f:
                f.write(res.text)

        if self.state != 'Start':
            self.clear()  # Clear every scraped filed to start again
            self.set_state('Start')
            self.process = Process(target=scrape, args=(
                self.repo.get_id(), self.start_urls))
            self.process.start()
            #self.process.join()     # Blocking execution -  frontend is waiting for response
            self.set_state('Done')  # Set state with in scrape method
            self.repo.parser.set_state('Ready')
            self.repo.exporter.set_state('Ready')
            self.repo.update()

    def stop_scrape(self):
        self.process.terminate()

    def restart_scrape(self):
        self.process.kill()
        self.start_scrape()


class Parser(Bubble):

    def __init__(self, repo, data=None):
        super().__init__(repo, data)
        if self.state == 'Ready':
            self.create_graph()
        self.graph = None
        self.datatable = DataTable()

    def create_graph(self):
        if not hasattr(self, 'graph') or self.graph is None:
            path_scraped = os.path.join(
                PATH_REPO, self.repo.get_id(), PATH_SCRAPED)
            first_file = os.listdir(path_scraped)[0]
            self.graph = Graph(os.path.join(path_scraped, first_file))
        return self.graph

    def expand_node(self, node_id):
        self.graph.expand_node(node_id)

    def del_node(self, node_id):
        self.graph.del_node(node_id)

    def add_column(self, column, node_id):
        xpath = self.graph.create_xpath(node_id)
        self.datatable.add_column(column, xpath)
        self.repo.exporter.rdf = RDF_API(self.datatable.create_response(self.repo.get_id(), all=True))

    def del_column(self, column):
        self.datatable.del_column(column)

    def clear(self):
        self.scraped_file_count = 0
        path = os.path.join(PATH_REPO, self.repo.get_id(), PATH_PARSED)
        files = os.listdir(path)
        for f in files:
            path_file = os.path.join(path, f)
            # print(path_file)
            os.remove(path_file)

class Exporter(Bubble):
    def __init__(self, repo, data=None):
        super().__init__(repo, data)
        self.name = 'Exporter'
        self.finished_file_count = 0
        self.total_file_count = self.get_total_file_count()

    def get_bubble(self):
        return {
            'state'               : self.state,
            'finished_file_count' : self.finished_file_count if self.state in ['Start', 'Done'] else None,
            'total_file_count'    : self.total_file_count if self.state in ['Start', 'Done'] else None,
        }

    def get_total_file_count(self):
        path_scraped = os.path.join(
            PATH_REPO, self.repo.get_id(), PATH_SCRAPED)
        total = len(os.listdir(path_scraped))
        return total

    def get_parsed_path(self):
        parsed_path = os.path.join(PATH_REPO, self.repo.get_id(), PATH_PARSED)
        parsed_file = os.path.join(
            parsed_path, '{}.{}'.format(self.repo.get_name(), 'json'))
        return parsed_file

    def start_export(self, graph, datatable):

        def soup_xpath(xpathstring, soupobject):
            pattern = re.compile(r'.*\[([0-9]*)\]')
            from_body = xpathstring.replace("/html/body", "")
            for item in from_body.split("/")[1:]:
                result = re.match(pattern, item)
                try:
                    if(result is not None):
                        soupobject = soupobject.find_all(item.split('[')[0], recursive=False)[
                            int(result.groups()[0]) - 1]
                    else:
                        soupobject = soupobject.find(item)
                except:
                    return ''
            return soupobject.text.strip().strip(u'\u200b')

        scraped_path = os.path.join(
            PATH_REPO, self.repo.get_id(), PATH_SCRAPED)
        scraped_file = os.listdir(scraped_path)
        data_table   = datatable.data_table

        #if self.state == 'Ready':
        self.finished_file_count = 0
        # print(scraped_file)
        parsed_data = []
        #self.set_state('Start')
        for file_name in scraped_file:
            graph = Graph(os.path.join(scraped_path, file_name))
            data = {'id': file_name.split('.')[0]}
            #print('Parsing file {}'.format(file_name))
            for row in data_table:
                #print('Soup xpath {}'.format(row))
                data[row] = soup_xpath(
                    data_table[row], graph.root_node.bs4_node)
            parsed_data.append(data)
            self.finished_file_count = self.finished_file_count+1
            self.repo.update()
            #print("finished files count: {}".format(self.finished_file_count))
        parsed_file = self.get_parsed_path()
        with open(parsed_file, 'w') as f:
            json.dump(parsed_data, f)
        #self.set_state('Done')
        return parsed_data
    
    def get_rdf(self):
        if 'rdf' not in self.__dict__:
            self.rdf = RDF_API(self.repo.parser.datatable.create_response(self.repo.get_id()))
        return self.rdf

