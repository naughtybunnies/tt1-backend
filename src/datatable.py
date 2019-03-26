import re
import os

from src.config import PATH_REPO,PATH_SCRAPED,PATH_PARSED

class DataTable(object):
    def __init__(self):
        self.data_table = {}
    
    def add_column(self, column, xpath):
        self.data_table[column] = xpath
    
    def del_column(self, column):
        self.data_table.pop(column)

    def clear_column(self):
        self.data_table = {}
