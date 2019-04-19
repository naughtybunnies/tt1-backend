import re
import os

from src.config import PATH_REPO, PATH_SCRAPED, PATH_PARSED
from src.graph import Graph


class DataTable(object):
    def __init__(self):
        self.data_table = {}

    def get_column(self):
        column = [col for col in self.data_table.keys()]
        return column

    def add_column(self, column, xpath):
        self.data_table[column] = xpath

    def del_column(self, column):
        self.data_table.pop(column)

    def clear_column(self):
        self.data_table = {}

    def create_response(self, repo_id, all=False):
        def soup_xpath(xpathstring, soupobject):
            pattern = re.compile(r'.*\[([0-9]*)\]')
            from_body = xpathstring.replace("/html/body", "")
            for item in from_body.split("/")[1:]:
                result = re.match(pattern, item)
                if(result is not None):
                    soupobject = soupobject.find_all(item.split('[')[0], recursive=False)[
                        int(result.groups()[0]) - 1]
                else:
                    soupobject = soupobject.find(item)
            return soupobject.text.strip().strip(u'\u200b')

        scraped_path = os.path.join(PATH_REPO, repo_id, PATH_SCRAPED)
        scraped_file = os.listdir(scraped_path)
        parsed_data = []
        n = len(scraped_file) if all is True else 5
        for file_count in range(n):
            try:
                graph = Graph(os.path.join(
                    scraped_path, scraped_file[file_count]))
                data = {'id': scraped_file[file_count].split('.')[0]}
                #print('Parsing file {}'.format(scraped_file[file_count]))
                for row in self.data_table:
                    #print('Soup xpath {}'.format(row))
                    data[row] = soup_xpath(
                        self.data_table[row], graph.root_node.bs4_node)
                parsed_data.append(data)
            except:
                pass
        return parsed_data
