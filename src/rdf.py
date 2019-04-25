from rdflib import URIRef, BNode, Literal
from rdflib import Namespace, Graph
from rdflib.namespace import FOAF, RDF

from src.config import PATH_VOCAB

import urllib
import json
import os

class RDF_API(object):
    def __init__(self, data):
        from rdflib import URIRef, Literal, Namespace, Graph
        from rdflib.namespace import FOAF, RDF
        
        self.baseURL = Namespace("http://rdf-api.com/")
        self.entityIdentifier = "id"
        
        self.requests = []
        self.data = data
        
        self.graph = Graph()
        
        self.vocabs = {'foaf': FOAF, 'rdf': RDF}
    
    def add_rule_using_column(self, predicate, object_column, as_type, add_transaction=True):
        p = self._parse_predicate(predicate)
        
        for row in self.data:
            s = self.baseURL[str(row[self.entityIdentifier]).replace(' ', '_')]

            if(as_type == 'literal'): o = Literal(row[object_column])
            elif(as_type == 'object'): o = self.baseURL[row[object_column]]
            else: o = self._parse_predicate(object_column)
            triplet = (s, p, o)

            self.graph.add(triplet)
        
        if(add_transaction): self.requests.append({"predicate": predicate, "object_column": object_column, "as_type": as_type})
    
    def set_baseURL(self, newBaseURL):
        self.baseURL = Namespace(newBaseURL.strip("/") + "/")
        self._re_render_graph()

    def set_entityIdentifier(self, newIdentifier):
        self.entityIdentifier = newIdentifier
        self._re_render_graph()
        
    def _re_render_graph(self):
        self.graph = Graph()
        for request in self.requests:
            self.add_rule_using_column(request["predicate"], request["object_column"], request["as_type"], add_transaction=False)
    
    def _parse_predicate(self, predicate):
        vocab, word = predicate.split(":")
        return self.vocabs[vocab][word]
    
    def serialize_graph(self, format='turtle'):
        graph_string = self.graph.serialize(format=format, encoding='UTF-8').decode()
        return graph_string

    def get_rules(self):
        rule = []
        for i, e in enumerate(self.requests):
            r = {
                'i' : i,
                's' : '{}{}'.format(self.baseURL, self.entityIdentifier),
                'p' : e['predicate'],
                'o' : '{}'.format(self.baseURL[e['object_column']]) if e['as_type'] == 'object' else e['object_column']
            }
            rule.append(r)
        return rule
    
    def remove_rule(self, index):
        self.requests.pop(index)
        self._re_render_graph()
        return self.get_rules()

    def get_vocabulary(self):
        vocabulary_json = os.listdir(PATH_VOCAB)
        data = {}
        for ns in vocabulary_json:
            with open('{}/{}'.format(PATH_VOCAB, ns), 'r') as f:
                data[ns.split('.')[0]] = json.load(f)
        return data