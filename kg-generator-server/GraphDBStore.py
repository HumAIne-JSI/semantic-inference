import random
from typing import *
from llama_index.core.graph_stores.types import GraphStore
from typing import Any, Dict, List, Optional, Protocol, TypedDict, runtime_checkable
from rdflib import Graph, URIRef, Literal, ConjunctiveGraph
from urllib.parse import quote_plus, unquote_plus
import re
import queue
from datetime import datetime, timedelta
import SPARQLWrapper
import aas_core3.jsonization as aas_jsonization
import aas_core3.types as aas_types


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
        self.all_query_time = 0
        self.sparql = SPARQLWrapper.SPARQLWrapper(self.sparql_endpoint)
        self.random_id = "c5nLE3vR"
        
    def generate_triples_from_json(self, subject, json_data, triples):
        if isinstance(json_data, dict):
            if 'id' in json_data.keys():
                subject = json_data['id']
            elif 'idShort' in json_data.keys():
                subject = json_data['idShort']
            rand_num_str = self.random_id + random.randint(0, 10000000000).__str__()
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

                    obj, proc_obj = self.generate_triples_from_json("a " + key + " entity", value, triples)
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
    
    def generate_triples_from_AAS_json(self, AAS_json, triples):
        print("HERE")
        environment = aas_jsonization.environment_from_jsonable(
            AAS_json
        )
        print("TU")

        def get_uri(text):
            return URIRef(self.random_uri + text)

        def add_triple(a, b, c):
            triple = map(lambda e : get_uri(quote_plus(str(e))), (a, b, c))
            a2, b2, c2 = triple
            triples.append({'readable': {'subject': a, 'predicate': b, 'object': c}, 'processed': {'subject': a2, 'predicate': b2, 'object': c2}})
        for e in environment.descend():
            # print(type(something) == aas_types.AssetAdministrationShell, dir(something))
            if (type(e) == aas_types.AssetAdministrationShell):
                if e.asset_information.asset_kind == aas_types.AssetKind.INSTANCE:
                    add_triple(e.id, "is instance of", e.derived_from.keys[0].value)
                for submodel in e.submodels:
                    add_triple(submodel.keys[0].value, f'is part of / describes', e.id)
                add_triple(e.id, "has description", e.description[0].text)
                add_triple(e.id, "has name", e.id_short)
            elif (type(e) == aas_types.Submodel):
                add_triple(e.id, "has name", e.id_short)
                add_triple(e.id, "has description", e.description[0].text)
                for submodel_element in e.submodel_elements:
                    add_triple(e.id, f'has "{submodel_element.id_short}" value', submodel_element.value)

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
        # print("TU", subj)
        # query = f"""
        #     PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        #     PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        #     SELECT ?a ?o
        #     WHERE {{
        #         SERVICE <{self.sparql_endpoint}> {{
        #             GRAPH ?g {{
        #                 <{uri}> ?a ?o .
        #             }}
        #         }}
        #         VALUES ?g {{<{self.graph_name}>}}
        #         FILTER(?a != rdfs:label && ?a != rdf:type) .
        #     }}
        #     LIMIT {limit}
        # """

        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT ?a ?o
            WHERE {{
                GRAPH <{self.graph_name}> {{
                    <{uri}> ?a ?o .
                }}
                FILTER(?a != rdfs:label && ?a != rdf:type) .
            }}
            LIMIT {limit}
        """
        

        self.sparql.method = 'POST'
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat('json')
        res = self.sparql.query().convert()['results']['bindings']
        return list(map(lambda tup : [tup['a']['value'], tup['o']['value']], res))
    
    def _get_prev(self, obj: str, limit = 1e18) -> List[List[str]]:
        uri = URIRef(obj)
        # print("TU", subj)
        # query = f"""
        #     PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        #     PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        #     SELECT ?a ?o
        #     WHERE {{
        #         SERVICE <{self.sparql_endpoint}> {{
        #             GRAPH ?g {{
        #                 <{uri}> ?a ?o .
        #             }}
        #         }}
        #         VALUES ?g {{<{self.graph_name}>}}
        #         FILTER(?a != rdfs:label && ?a != rdf:type) .
        #     }}
        #     LIMIT {limit}
        # """

        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT ?s ?a
            WHERE {{
                GRAPH <{self.graph_name}> {{
                    ?s ?a <{uri}> .
                }}
                FILTER(?a != rdfs:label && ?a != rdf:type) .
            }}
            LIMIT {limit}
        """
        

        self.sparql.method = 'POST'
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat('json')
        res = self.sparql.query().convert()['results']['bindings']
        return list(map(lambda tup : [tup['s']['value'], tup['a']['value']], res))
    
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
        self, subj: str, rel_map, depth: int = 6, limit: int = 100
    ) -> List[List[str]]:
        start_time = datetime.now()
        print("in321123", subj, start_time, depth, limit)
        q = queue.Queue()
        q.put((None, None, None, 0, None, subj))
        vis = set()
        while not q.empty():
            subj, pred, obj, cdepth, prev, current = q.get()
            if cdepth > depth:
                break
            if cdepth > 0:
                if self.unURIfy(subj) not in rel_map:
                    rel_map[self.unURIfy(subj)] = []
                rel_map[self.unURIfy(subj)].append([self.unURIfy(subj), self.unURIfy(pred), self.unURIfy(obj)])
            if current not in vis and limit > 0:
                for pred, next_obj in self.get(current, limit):
                        if next_obj == prev:
                            continue
                        q.put((current, pred, next_obj, cdepth + 1, current, next_obj))
                        limit -= 1
                        # print(limit)
                        if limit == 0:
                            break
                for prev_subj, pred in self._get_prev(current, limit):
                        if prev_subj == prev:
                            continue
                        q.put((prev_subj, pred, current, cdepth + 1, current, prev_subj))
                        limit -= 1
                        # print(limit)
                        if limit == 0:
                            break
            vis.add(obj)
        print("TULE")


    def search_for_term(self, term, limit = 3):
        print("searchin", term)
        term = ''.join([' ' if char in "()[]-+&!\'\"\*\?{}[]~\\" else char for char in term]).strip()
        term = re.sub(r'\s+', ' ', term)
        query = f"""
            PREFIX luc: <http://www.ontotext.com/connectors/lucene#>
            PREFIX luc-index: <http://www.ontotext.com/connectors/lucene/instance#>
            SELECT ?entity {{
                SERVICE <{self.sparql_endpoint}> {{
                    ?search a luc-index:search ;
                        luc:query 'search: {' '.join(word + '~2' for word in term.split())}' ;
                        luc:limit "{limit * 3 // 2}" ;
                        luc:entities ?entity .
                    ?entity luc:score ?score
                    filter(?score >= 0.4)
                }}
            }}
        """ 
        
        res1 = list(map(lambda tup : tup[0], list(self.graph_read.query(query))))
        print(res1)
        query2 = f"""
            PREFIX :<http://www.ontotext.com/graphdb/similarity/>
            PREFIX inst:<http://www.ontotext.com/graphdb/similarity/instance/>
            PREFIX pubo: <http://ontology.ontotext.com/publishing#>

            SELECT ?documentID ?score {{
                ?search a inst:search-text ;
                        :searchTerm "{term}" ;
                        :searchParameters "-numsearchresults {limit}";
                        :documentResult ?result .
                ?result :value ?documentID ;
                        :score ?score .
            }}
        """
        self.sparql.method = 'GET'
        self.sparql.setQuery(query2)
        self.sparql.setReturnFormat('json')
        res2 = list(map(lambda tup : tup['documentID']['value'], self.sparql.query().convert()['results']['bindings']))
        print(res2)
        return res2 + res1


    def get_rel_map(
        self, subjs: Optional[List[str]] = None, depth: int = 6, limit: int = 100
    ) -> Dict[str, List[List[str]]]:
        """Get depth-aware rel map."""
        print("HERE", subjs)
        if subjs is None:
            subjs = self._get_all_subjs()
        new_subjs = []
        for subj in subjs:
            new_subjs += self.search_for_term(subj)
        subjs = new_subjs
        # subjs = self.search_for_term(", ".join(subjs), 1)
        rel_map = {}
        print("here", subjs)
        for subj in set(subjs):
            self._get_rel_map(subj, rel_map, depth=6, limit=100)
            
        # return self._data.get_rel_map(subjs=subjs, depth=depth, limit=limit)
                    # TBD, truncate the rel_map in a spread way, now just truncate based
        # on iteration order
        print("TU")
        rel_count = 0
        return_map = {}
        for subj in rel_map:
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
            return res
        if self.value_uri in uri:
            return unquote_plus(uri.replace(self.value_uri, ""))
        if self.predicate_uri in uri:
            return unquote_plus(uri.replace(self.predicate_uri, ""))