from bs4 import BeautifulSoup

class ParseError(Exception):
    def __init__(self, message):
        self.message = message

class Graph(object):
    def __init__(self, html_path: str):
        self.nodes = {}
        self.edges = []
        
        self.root_node = self.create_root_node(html_path)
        self.add_node(self.root_node)
        
    def create_root_node(self, html_path: str):
        '''Read file from input html_path into Node object.'''
        from bs4 import BeautifulSoup
        
        try:
            with open(html_path, 'r') as fin:
                soup = BeautifulSoup(fin.read(), 'lxml')      #  Parse file into bs4 soup object.
                root_bs4 = soup.body                          #  Create tag object from body.
                root_node = Node(root_bs4)                    #  Create self-defined Node.
            return root_node
        except FileNotFoundError:
            raise ParseError("File {} not found in directory".format(html_path))
    
    def add_node(self, node_object):
        node_id = node_object._id                  #  get id  
        self.nodes.update({node_id: node_object})  #  add new node into self.node

    def del_node(self, node_id):
        
        parent_edge = [e for e in self.edges if e[1]==node_id][0]
        
        children_edge = [e for e in self.edges if e[0]==node_id ]
        for e in children_edge:
            # print('delete {} from {}'.format(e[1], e[0]))
            self.edges = [ edge for edge in self.edges if not(edge==e)]
            del self.nodes[e[1]]
        #print('delete {} from {}'.format(parent_edge[1], parent_edge[0]))
        self.edges = [ edge for edge in self.edges if not(edge==parent_edge)]
        del self.nodes[node_id]

    def add_edge(self, id_node_from, id_node_to):
        self.edges.append((id_node_from, id_node_to))  #  append tuple of id_node_from and id_node_to
    
        
    def expand_node(self, node_id):
        node = self.nodes.get(node_id)  #  get node to be expanded from self.node
        children = node.get_children()  #  create bs4 objects of children
        
        for c in children:
            c_node = Node(c)                   #  create self-defined node
            c_node_id = c_node._id             #  get id of new node
            self.add_node(c_node)              #  add new node into self.node
            self.add_edge(node_id, c_node_id)  #  connect parent node with child node
            
    def create_response(self):
        response = {"nodes": [item[1].render_response() for item in self.nodes.items()], 
                    "edges": [{"from": item[0], "to": item[1]} for item in self.edges]}
        
        return response

    def create_xpath(self, node_id = None):
        if node_id == None:
            xpath = [ self.xpath_soup(self.nodes[n].bs4_node) for n in self.nodes]
        else:
            xpath = self.xpath_soup(self.nodes[node_id].bs4_node)
            
        return xpath

    def xpath_soup(self, element):
        components = []
        child = element if element.name else element.parent
        for parent in child.parents:
            siblings = parent.find_all(child.name, recursive=False)
            components.append(
                child.name
                if siblings == [child] else
                '%s[%d]' % (child.name, 1 + siblings.index(child))
                )
            child = parent
        components.reverse()
        return '/%s' % '/'.join(components)
        
class Node(object):
    def __init__(self, bs4_tag):
        self.bs4_node = bs4_tag       #  Keep bs4 tag object for navigating html tree.
        self._id = id(self)           #  Create node id for response.
        self.tag_name = bs4_tag.name  #  Create tag name of this node.
        self.html_string = str(bs4_tag)      #  Create html string.
        self.text = bs4_tag.text      #  Create text of the file.
        
    def render_response(self):
        response = {"id": self._id, "label": self.tag_name, "title": self.text}
        while '\n\n' in response['title']:  # confiscate \n\n from the text until there is only one \n in the response
            response['title'] = response['title'].replace('\n\n', '\n')
        response['title'] = response['title'].strip()
        return response

    def delete_node(self):
        del self

    def get_children(self, remove_non_informative=True):
        def is_non_informative(node_navigatable_string):
            if(len(str(node_navigatable_string).strip()) == 0):  #  empty field
                return True
            if(node_navigatable_string.name is None):  #  remove comment, non tag
                return True
            if(node_navigatable_string.name in ['script', 'nav', 'header', 'footer', 'noscript']):  #  remove script
                return True
            if(len(node_navigatable_string.text) == 0):
                return True

        children = list(self.bs4_node.children)
        if(remove_non_informative):
            children = [c for c in children if not is_non_informative(c)]
        return children            