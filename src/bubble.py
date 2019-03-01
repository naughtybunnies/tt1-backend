from multiprocessing import Process, Manager, Value
from urllib import parse
from src.config import PATH_REPO, PATH_SCRAPED 

import requests
import os
import re
import time

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
                'state' :   'Ready',
                'scraped_file_count' : 0,
                'total_file_count'   : 0,
                'start_urls'         : []
            }
        super().__init__(repo, data)
        self.name  = 'Scraper'

    def get_bubble(self):
        return {
            'state' :   self.get_state(),
            'scraped_file_count'    :   self.get_scraped_file_count(),
            'total_file_count'      :   self.get_total_file_count(),
            'start_urls'            :   self.get_start_urls()
        }
    
    def get_scraped_file_count(self):
        path_scraped = os.path.join(PATH_REPO, self.repo.get_id(), PATH_SCRAPED)
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

    def start_scrape(self):
        def clear():       
            self.scraped_file_count = 0           
            path = os.path.join(PATH_REPO, self.repo.get_id(), PATH_SCRAPED)
            files = os.listdir(path)
            for f in files:
                path_file = os.path.join(path, f)
                #print(path_file)
                os.remove(path_file)

        def scrape(repo, start_urls):
            with requests.Session() as s:
                for url in start_urls:
                    res = s.get(url['url'])
                    print('{} {}'.format(res.url, res.status_code))
                    save_file(repo, res, url['key'])

        def save_file(repo, res, key):
            path_scraped = os.path.join(PATH_REPO, repo, PATH_SCRAPED)
            path_file = os.path.join(path_scraped, str(key))
            with open(path_file, 'w') as f:
                f.write(res.text)

        if self.state != 'Start':
            clear() #   Clear every scraped filed to start again
            self.set_state('Start')
            self.process = Process(target=scrape, args=(self.repo.get_id(), self.start_urls))
            self.process.start()
            self.process.join()
            self.set_state('Done')    

    def stop_scrape(self):
        self.process.terminate()
    
    def restart_scrape(self):
        self.process.kill()
        self.start_scrape()

class Parser(Bubble):
    def __init__(self, repo, data=None):
        super().__init__(repo, data)
        self.name  = 'Parser'

class Exporter(Bubble):
    def __init__(self, repo, data=None):
        super().__init__(repo, data)
        self.name  = 'Exporter'