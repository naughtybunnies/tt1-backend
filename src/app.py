from src.config import PATH_REPO, PATH_SCRAPED
from src.repository import Repository
import os


class App(object):
    def __init__(self):
        '''App will create repositories folder to keep repositories.'''
        try:
            os.mkdir(PATH_REPO)
        except FileExistsError:
            pass
        self.repo = self.get_repo()  # Assign existing repositories to self

    def create_repo(self, name):
        print('New repo is created')
        for repo in self.repo:
            if repo.get_name() == name:
                raise ValueError('A repository with this name already exists.')
        new_repo = Repository(name=name)
        self.repo.append(new_repo)

    def rename_repo(self, repo, new_name):
        repo.rename(new_name)

    def delete_repo(self, repo):
        print('Delete repo')
        repo.delete()
        self.repo.remove(repo)

    def get_repo(self, id=None, name=None):
        if name is not None:
            for repo in self.repo:
                if repo.get_name() == name:
                    return repo
        elif id is not None:
            for repo in self.repo:
                if repo.get_id() == id:
                    return repo
            return None
        else:  # From App init
            repo_id = os.listdir(PATH_REPO)               # Read files in repositories folder
            repo = [Repository(id=id) for id in repo_id]  # Create Repositories objec from file
            return repo

    def set_url(self, repo, url, start_key, end_key):
        repo.set_url(url, start_key, end_key)

    def set_file(self, repo, start_urls):
        repo.set_file(start_urls)
