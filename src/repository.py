from src.config import PATH_REPO, PATH_SCRAPED, PATH_PARSED
from src import bubble

import uuid
import os
import json
import shutil
import datetime

class Repository(object):
    def __init__(self, name=None, id=None):
        if name is not None:  # Create new repository
            self.id = str(uuid.uuid4())
            self.name = name
            self.createdDate = datetime.datetime.now().strftime("%d-%b-%Y")
            self.create_directory(self.id)

            # Assign this repo to all the bubble
            self.scraper  = bubble.Scraper(self)
            self.parser   = bubble.Parser(self)
            self.exporter = bubble.Exporter(self)

            # Update this repo's bubble status
            self.set_bubble({
                'scraper': self.scraper.get_bubble(),
                'parser': self.parser.get_bubble(),
                'exporter': self.exporter.get_bubble()
            })

            # Save a new index.json file for the repo
            self.update()
        # if
        elif id is not None:  # Retrieve existing repositories
            path = os.path.join(PATH_REPO, id)
            f = open('{}/index.json'.format(path), 'r')
            data = json.load(f)
            f.close()
            self.id = data['id']
            self.name = data['name']
            self.bubble = data['bubble']
            self.scraper  = bubble.Scraper(self, data['bubble']['scraper'])
            self.parser   = bubble.Parser(self, data['bubble']['parser'])
            self.exporter = bubble.Exporter(self, data['bubble']['exporter'])

    def set_id(self, id):
        self.id = id

    def set_name(self, name):
        self.name = name

    def set_bubble(self, bubble):
        try:
            self.bubble.update(bubble)
        except AttributeError:
            self.bubble = bubble

    def set_url(self, url, start_key, end_key):
        self.scraper.set_url(url, start_key, end_key)
        self.update()

    def submit_file(self, start_urls):
        self.scraper.submit_file(start_urls)
        self.update()

    def discard_file(self):
        self.scraper.discard_file()
        self.update()

    def set_file(self, start_urls):
        self.scraper.set_file(start_urls)
        self.update()

    def update(self):
        path = os.path.join(PATH_REPO, self.id)
        data = {
            'id'   : self.id,
            'name' : self.name,
            'bubble': {
                'scraper'  :   self.scraper.get_bubble(),
                'parser'   :   self.parser.get_bubble(),
                'exporter' :   self.exporter.get_bubble(),
            },
            'createdDate'  :   self.createdDate
        }
        self.id = data['id']
        self.name = data['name']
        self.state = data['bubble']
        f = open('{}/index.json'.format(path), 'w')
        json.dump(data, f)
        f.close()

    def create_directory(self, directory):
        try:
            # Create repo's root directory
            path = os.path.join(PATH_REPO, directory)
            os.mkdir(path)
            # Create repo's scraped directory to save files from scraper
            path_scraped = os.path.join(path, PATH_SCRAPED)
            os.mkdir(path_scraped)
            # Create repo's scraped directory to save files from parser
            path_parsed = os.path.join(path, PATH_PARSED)
            os.mkdir(path_parsed)
        except FileExistsError as e:
            print('{}'.format(e))

    def rename(self, new_name):
        self.name = new_name
        self.update()
        print('The repo was renamed to {}'.format(new_name))
        return 'OK'

    def delete(self):
        path = os.path.join(PATH_REPO, self.get_id())
        shutil.rmtree(path)
        print('The repo {} was deleted'.format(self.name))
        return 'OK'

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_bubble(self):
        return {
            'scraper': self.scraper.get_bubble(),
            'parser': self.parser.get_bubble(),
            'exporter': self.exporter.get_bubble()
        }

    def get_createdDate(self):
        return self.createdDate

    def get_status(self):
        self.update()
        return {
            'id'     : self.get_id(),
            'name'   : self.get_name(),
            'bubble' : self.get_bubble(),
            'createdDate': self.get_createdDate()
        }

    def start_scrape(self):
        self.scraper.start_scrape()

    def start_export(self):
        return self.exporter.start_export(self.parser.graph, self.parser.datatable)
