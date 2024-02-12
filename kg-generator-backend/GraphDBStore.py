import random
from typing import *
from llama_index.graph_stores.types import GraphStore
from typing import Any, Dict, List, Optional, Protocol, TypedDict, runtime_checkable
from rdflib import Graph, URIRef, Literal, ConjunctiveGraph
from urllib.parse import quote_plus, unquote_plus
import re
import queue


class BasicTriple(TypedDict):
    subject: str
    predicate: str
    object: str

class Triple(TypedDict):
    readable: BasicTriple
    processed: BasicTriple

class GraphDBStore(GraphStore):
    """Simple Graph Store.

    In this graph store, triplets are stored within a simple, in-memory dictionary.

    Args:
        simple_graph_store_data_dict (Optional[dict]): data dict
            containing the triplets. See SimpleGraphStoreData
            for more details.
    """

    def __init__(
        self,
        sparql_endpoint,
        graph_name = "http://example.com",
        random_uri = "http://www.entity-with-random-id/",
        value_uri = "http://www.value/",
        predicate_uri = "http://www.predicate/",
        # data: Optional[SimpleGraphStoreData] = None,
    ) -> None:
        self.random_uri = random_uri
        self.value_uri = value_uri
        self.predicate_uri = predicate_uri
        self.graph_name = graph_name
        self.graph_write = Graph(store='SPARQLUpdateStore', identifier=self.graph_name)
        self.graph_write.open(f'{sparql_endpoint}/statements')
        self.graph_read = ConjunctiveGraph()
        self.sparql_endpoint = sparql_endpoint
        
    def generate_triples_from_json(self, subject, json_data, triples):
        if isinstance(json_data, dict):
            if 'id' in json_data.keys():
                subject = json_data['id']
            elif 'idShort' in json_data.keys():
                subject = json_data['idShort']
            rand_num_str = random.randint(0, 10000000000).__str__()
            subject = subject + " " + rand_num_str
            processed_subject = self.random_uri + quote_plus(subject)
            for key, val in json_data.items():
                is_list = True
                if not isinstance(val, list):
                    val = [val]
                    is_list = False
                for value in val:
                    def add_triple(sub, pred, obj, processed_subject, processed_predicate, processed_object):
                        triples.append({'readable': {'subject': sub, 'predicate': pred, 'object': obj}, 'processed': {'subject': processed_subject, 'predicate': processed_predicate, 'object': processed_object}})

                    obj, proc_obj = self.generate_triples_from_json("a" + key + " entity", value, triples)
                    predVal1 = "has " + key
                    pred1 = self.predicate_uri + quote_plus(predVal1)
                    add_triple(subject, predVal1, obj, processed_subject, pred1, proc_obj)
                    predVal2 = ("is one of " if is_list else "is ") + key + " of"
                    pred2 = self.predicate_uri + quote_plus(predVal2)
                    add_triple(obj, predVal2, subject, proc_obj, pred2, processed_subject)
        else:
            subject = str(json_data)
            processed_subject = self.value_uri + quote_plus(subject)
        return (subject, processed_subject)

    def _delete_all(self):
        self.graph_write.remove((None, None, None))
        self.graph_write.commit()

    @property
    def client(self) -> None:
        """Get client.
        Not applicable for this store.
        """
        return

    def remove_pref(self, uri):
        return unquote_plus(uri.replace(self.url_pref + "/", ""))

    def get(self, subj: str, limit = 1e18) -> List[List[str]]:
        uri = URIRef(subj)
        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT ?a ?o
            WHERE {{
                SERVICE <{self.sparql_endpoint}> {{
                    GRAPH ?g {{
                        <{uri}> ?a ?o .
                    }}
                }}
                VALUES ?g {{<{self.graph_name}>}}
                FILTER(?a != rdfs:label && ?a != rdf:type) .
            }}
            LIMIT {limit}
        """

        # print("GETTING FOR ", subj, list(map(lambda tup : [self.remove_pref(tup[0]), self.remove_pref(tup[1])], list(res))))
        # print(query)
        return list(map(lambda tup : [tup[0], tup[1]], list(self.graph_read.query(query))))
    
    def _get_all_subjs(self) -> List[str]:
        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT DISTINCT ?s
            WHERE {{    
                SERVICE <{self.sparql_endpoint}> {{
                    GRAPH ?g {{
                        ?s ?a ?o .
                    }}
                }}
                VALUES ?g {{<{self.graph_name}>}}
                FILTER(?a != rdfs:label && ?a != rdf:type) .
            }}
        """
        return list(map(lambda tup : tup[0], list(self.graph_read.query(query))))
        
    def _get_rel_map(
        self, subj: str, depth: int = 2, limit: int = 100
    ) -> List[List[str]]:
        print("in", subj)
        depth_of = {}
        q = queue.Queue()
        q.put((subj, None, None, 0))
        rel_map = []
        while not q.empty():
            obj, subj, pred, cdepth = q.get()
            if cdepth > depth:
                break
            if depth_of.get(obj) is not None:
                continue
            depth_of[obj] = cdepth
            if cdepth > 0:
                rel_map.append([self.unURIfy(subj), self.unURIfy(pred), self.unURIfy(obj)])
            for pred, next_obj in self.get(obj, limit):
                    q.put((next_obj, obj, pred, cdepth + 1))
        return rel_map

    def search_for_term(self, term, limit = 20):
        term = ''.join([' ' if char in "()[]-+&!\'\"\*\?{}[]~\\" else char for char in term]).strip()
        term = re.sub(r'\s+', ' ', term)
        term = ' '.join(word + '~2' for word in term.split())
        query = f"""
            PREFIX luc: <http://www.ontotext.com/connectors/lucene#>
            PREFIX luc-index: <http://www.ontotext.com/connectors/lucene/instance#>
            SELECT ?entity {{
                SERVICE <{self.sparql_endpoint}> {{
                    ?search a luc-index:search ;
                        luc:query 'search: {term}' ;
                        luc:limit "{limit}" ;
                        luc:entities ?entity .
                    ?entity luc:score ?score
                    filter(?score >= 0.6)
                }}
            }}
        """ 
        print(term, list(map(lambda tup : tup[0], list(self.graph_read.query(query)))))
        print(query)
        return list(map(lambda tup : tup[0], list(self.graph_read.query(query))))      


    def get_rel_map(
        self, subjs: Optional[List[str]] = None, depth: int = 6, limit: int = 100
    ) -> Dict[str, List[List[str]]]:
        """Get depth-aware rel map."""
        #print("HERE", subjs)
        if subjs is None:
            subjs = self._get_all_subjs()
        new_subjs = []
        for subj in subjs:
            new_subjs += self.search_for_term(subj)
        subjs = new_subjs
        rel_map = {}
        for subj in subjs:
            if subj not in rel_map:
                rel_map[self.unURIfy(subj)] = self._get_rel_map(subj, depth=depth, limit=limit)
        # return self._data.get_rel_map(subjs=subjs, depth=depth, limit=limit)
                    # TBD, truncate the rel_map in a spread way, now just truncate based
        # on iteration order
        rel_count = 0
        return_map = {}
        for subj in rel_map:
            if rel_count + len(rel_map[subj]) > limit:
                return_map[subj] = rel_map[subj][: limit - rel_count]
                break
            else:
                # print(subj)
                return_map[subj] = rel_map[subj]
                rel_count += len(rel_map[subj])
        print("to return", return_map)
        return return_map
    
    def get_uri(self, el: str, add_label=False) -> str:
        oldEl = el
        if (not el.startswith(self.url_pref)):
            el = f'{self.url_pref}/{quote_plus(el)}'
        uri = URIRef(el)
        
        if add_label:
            label_uri = URIRef("http://www.w3.org/2000/01/rdf-schema#label")
            self.graph_write.remove((uri, label_uri, None))
            self.graph_write.add((uri, label_uri, Literal(oldEl)))
            type_uri = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
            self.graph_write.remove((uri, type_uri, None))
            self.graph_write.add((uri, type_uri, URIRef(self.graph_name)))
        
        return uri

    def get_uris(self, subj: str, rel: str, obj: str) -> (str, str, str):
        return (self.get_uri(subj, True), self.get_uri(rel, True), self.get_uri(obj, True))
    
    
    def upsert_triplet(self, subj: str, rel: str, obj: str) -> None:
        print("inserting", subj, rel, obj)
        self.graph_write.add(self.get_uris(subj, rel, obj))
        self.graph_write.commit()

    def add_auxilary_triples(self, readable, processed, graph) -> None:
        label_uri = URIRef("http://www.w3.org/2000/01/rdf-schema#label")
        # self.graph_write.remove((uri, label_uri, None))
        graph.add((URIRef(processed), URIRef(label_uri), Literal(readable)))
        type_uri = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
        # self.graph_write.remove((uri, type_uri, None))
        graph.add((URIRef(processed), URIRef(type_uri), URIRef(self.graph_name)))

    def _upsert_triples(self, triples: List[Triple]) -> None:
        graph = Graph()
        for triple in triples:
            print(triple)
            for key in triple['readable']:
                print(key)
                self.add_auxilary_triples(triple['readable'][key], triple['processed'][key], graph)
            proc_triple = triple['processed']
            print(proc_triple)
            graph.add((URIRef(proc_triple['subject']), URIRef(proc_triple['predicate']), URIRef(proc_triple['object'])))
        self.graph_write += graph

    def delete(self, subj: str, rel: str, obj: str) -> None:
        self.graph_write.remove(self.get_uris(subj, rel, obj))
        self.graph_write.commit()

    def persist(
        self
    ) -> None:
        """Persist the SimpleGraphStore to a directory."""
        self.graph_write.commit()
        # fs = fs or self._fs
        # dirpath = os.path.dirname(persist_path)
        # if not fs.exists(dirpath):
        #     fs.makedirs(dirpath)

        # with fs.open(persist_path, "w") as f:
        #     json.dump(self._data.to_dict(), f)

    def get_schema(self, refresh: bool = False) -> str:
        """Get the schema of the SimpleIt returns many results, some of which are “The Empire Strikes Back” and “Return of the Jedi”. This illustrates how full-text search tuned to a specific language (in this case English) is able to match “striking” to “strikes” and “jedis” to “jedi”. Graph store."""
        raise NotImplementedError("SimpleGraphStore does not support get_schema")

    def query(self, query: str, param_map: Optional[Dict[str, Any]] = {}) -> Any:
        """Query the Simple Graph store."""
        raise NotImplementedError("SimpleGraphStore does not support query")
    def unURIfy(self, uri):
        if self.random_uri in uri:
            res = unquote_plus(uri.replace(self.random_uri, ""))
            random_id = res.split()[-1]
            return res.replace(random_id, "(ID for discerning, don't show it to user: " + random_id + ")")
        if self.value_uri in uri:
            return unquote_plus(uri.replace(self.value_uri, ""))
        if self.predicate_uri in uri:
            return unquote_plus(uri.replace(self.predicate_uri, ""))