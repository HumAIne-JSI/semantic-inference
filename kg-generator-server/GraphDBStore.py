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
import math


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
        frequent_predicate_uri="http://www.frequent-predicate/"
        # data: Optional[SimpleGraphStoreData] = None,
    ) -> None:
        self.random_uri = random_uri
        self.value_uri = value_uri
        self.predicate_uri = predicate_uri
        self.frequent_predicate_uri = frequent_predicate_uri
        self.graph_name = graph_name
        self.graph_write = Graph(store='SPARQLUpdateStore', identifier=self.graph_name)
        self.graph_write.open(f'{sparql_endpoint}/statements')
        self.graph_read = ConjunctiveGraph()
        self.sparql_endpoint = sparql_endpoint
        self.all_query_time = 0
        self.sparql = SPARQLWrapper.SPARQLWrapper(self.sparql_endpoint)
        self.random_id = "c5nLE3vR"
        self.quantity = 100
        self.width = 3
        self.score_weight = 0
        
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

    
        def get_uri(text, is_literal=False, is_frequent_predicate=False):
            if is_frequent_predicate:
                return URIRef(self.frequent_predicate_uri + text)
            if is_literal:
                return URIRef(self.value_uri + text)
            return URIRef(self.random_uri + text)

        def add_triple(a, b, c, last_is_literal=False, is_frequent_predicate=False):
            triple = map(lambda e : get_uri(quote_plus(str(e[1])), True if last_is_literal and e[0] == 2 else False, True if is_frequent_predicate and e[0] == 1 else False), enumerate((a, b, c)))
            a2, b2, c2 = triple
            triples.append({'readable': {'subject': a, 'predicate': b, 'object': c}, 'processed': {'subject': a2, 'predicate': b2, 'object': c2}})
        for e in environment.descend():
            # print(type(something) == aas_types.AssetAdministrationShell, dir(something))
            if (type(e) == aas_types.AssetAdministrationShell):
                if e.asset_information.asset_kind == aas_types.AssetKind.INSTANCE:
                    add_triple(e.id, "is instance of", e.derived_from.keys[0].value, False, True)
                for submodel in e.submodels:
                    add_triple(submodel.keys[0].value, f'is part of / describes', e.id)
                add_triple(e.id, "has description", e.description[0].text, True)
                add_triple(e.id, "has name", e.id_short, True)
            elif (type(e) == aas_types.Submodel):
                add_triple(e.id, "has name", e.id_short, True)
                add_triple(e.id, "has description", e.description[0].text, True)
                for submodel_element in e.submodel_elements:
                    add_triple(e.id, f'has "{submodel_element.id_short}" value', submodel_element.value, True)

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
                FILTER(?a != rdfs:label && ?a != rdf:type && !STRSTARTS(STR(?a), "http://www.frequent-predicate/")) .
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
            }}r'], ['ykrUKaDzl2', 'is part of / describes', 'RobTefdT54']], '8ThMlVw1Fo': [['8ThMlVw1Fo', 'has "Manufacturer Name" value', 'QuantumTech Industries'], ['8ThMlVw1Fo', 'has description', 'Manufacturer of the asset'], ['8ThMlVw1Fo', 'has name', 'Manufacturer'], ['8ThMlVw1Fo', 'is part of / describes', 'PpxiMUowBX']], 'wSu3w9Cf0p': [['wSu3w9Cf0p', 'has "Manufacturer Name" value', 'QuantumTech Industries'], ['wSu3w9Cf0p', 'has description', 'Manufacturer of the asset'], ['wSu3w9Cf0p', 'has name', 'Manufacturer'], ['wSu3w9Cf0p', 'is part of / describes', 'anTYJk2Txy']], 'hTWL32OBPS': [['hTWL32OBPS', 'has "Manufacturer Name" value', 'QuantumTech Industries'], ['hTWL32OBPS', 'has description', 'Manufacturer of the asset'], ['hTWL32OBPS', 'has name', 'Manufacturer'], ['hTWL32OBPS', 'is part of / describes', '6LbmY1kOXv']], '3qL4Ma0fc1': [['3qL4Ma0fc1', 'has "Manufacturer Name" value', 'QuantumTech Industries'], ['3qL4Ma0fc1', 'has description', 'Manufacturer of the asset'], ['3qL4Ma0fc1', 'has name', 'Manufacturer'], ['3qL4Ma0fc1', 'is part of / describes', 'EAWOfqrkar']], 'qW5LIV3xWi': [['qW5LIV3xWi', 'has "Manufacturer Name" value', 'QuantumTech Industries'], ['qW5LIV3xWi', 'has description', 'Manufacturer of the asset'], ['qW5LIV3xWi', 'has name', 'Manufacturer'], ['qW5LIV3xWi', 'is part of / describes', 'mUqBWg57ho']], 'WrDvpiHAIN': [['WrDvpiHAIN', 'has "Manufacturer Name" value', 'QuantumTech Industries'], ['WrDvpiHAIN', 'has description', 'Manufacturer of the asset'], ['WrDvpiHAIN', 'has name', 'Manufacturer'], ['WrDvpiHAIN', 'is part of / describes', '7puiJHpoHy']], 'PXmz83Yluq': [['PXmz83Yluq', 'has "Required Current in amperes" value', '2']], 'dk8bGGQa9k': [['dk
        """
        return list(map(lambda tup : tup[0], list(self.graph_read.query(query))))
        
    def _get_rel_map(
        self, subj: str, rel_map, depth: int = 6, limit: int = 50
    ) -> List[List[str]]:
        start_time = datetime.now()
        print("in321123", subj, start_time, depth, limit)
        q = queue.Queue()
        q.put((None, None, None, 0, None, subj))
        vis = set()
        used = 0
        while not q.empty():
            subj, pred, obj, cdepth, prev, current = q.get()
            # print(subj, pred, obj, cdepth, prev, current)
            if cdepth > depth:
                break
            if cdepth > 0:
                if self.unURIfy(subj) not in rel_map:
                    rel_map[self.unURIfy(subj)] = []
                triple = [self.unURIfy(subj), self.unURIfy(pred), self.unURIfy(obj)]
                if triple not in rel_map[self.unURIfy(subj)]:
                    rel_map[self.unURIfy(subj)].append([self.unURIfy(subj), self.unURIfy(pred), self.unURIfy(obj)])
                    print([self.unURIfy(subj), self.unURIfy(pred), self.unURIfy(obj)])
                    used += 1
                    if used >= limit:
                        break
            if current not in vis and limit > 0:
                for pred, next_obj in self.get(current, limit):
                        if next_obj == prev:
                            continue
                        q.put((current, pred, next_obj, cdepth + 1, current, next_obj))
            
                if cdepth == 0 or not current.startswith(self.value_uri):
                    for prev_subj, pred in self._get_prev(current, limit):
                            if prev_subj == prev:
                                continue
                            q.put((prev_subj, pred, current, cdepth + 1, current, prev_subj))
            vis.add(obj)
        
        return limit


    def search_for_terms(self, terms, limit = 3):
        print("searchin", terms)
        map(lambda term : re.sub(r'\s+', ' ', ''.join([' ' if char in "()[]-+&!\'\"\*\?{}[]~\\" else char for char in term]).strip()), terms)

        query = f"""
            PREFIX retr: <http://www.ontotext.com/connectors/retrieval#>
            PREFIX retr-index: <http://www.ontotext.com/connectors/retrieval/instance#>

            SELECT * {{
                [] a retr-index:gpt-search ;
                retr:query '''
            {{
              "queries": [
                {''.join(map(lambda term : f'''{{"query": "{term}",}},''', terms))}
              ]
            }}
        ''' ;
                retr:limit {self.width};
                retr:entities ?entity .
                ?entity retr:score ?score
            }}
        """
        print(query)
        self.sparql.method = 'GET'
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat('json')
        print(self.sparql.query().convert())
        print("tu")
        res2 = list(map(lambda tup : (tup['entity']['value'], tup['score']['value']), self.sparql.query().convert()['results']['bindings']))
        print(res2)
        return res2


    def get_rel_map(
        self, subjs: Optional[List[str]] = None, depth: int = 6, limit: int = 2000
    ) -> Dict[str, List[List[str]]]:
        """Get depth-aware rel map."""
        print("HERE", subjs)

        if subjs is None:
            subjs = self._get_all_subjs()
        new_subjs = self.search_for_terms(subjs)
        new_subjs = list(set(new_subjs))
        subj_to_score = {}
        for subj, score in new_subjs:
            if subj not in subj_to_score:
                subj_to_score[subj] = float(score)
            else:
                subj_to_score[subj] = max(subj_to_score[subj], float(score))
        print(new_subjs)
        new_subjs = list(set(map(lambda t : t[0], new_subjs)))
        new_subjs = sorted(new_subjs, key=lambda subj:subj_to_score[subj], reverse=True)
        print(new_subjs)
        subjs = new_subjs
        # subjs = self.search_for_term(", ".join(subjs), 1)
        rel_map = {}
        limit = self.quantity
        left = limit
        subjs = subjs[:self.width]
        print("AAAABCD", self.width)
        while left > 0 and len(subjs) > 0:
            taken = 0
            to_del = {}
            to_take = []
            for i in range(len(subjs)):
                to_take.append(math.exp(subj_to_score[subjs[i]] * self.score_weight))
                print(i, to_take[i], subj_to_score[subjs[i]], subjs[i])
            sum_weights = sum(to_take)
            for i in range(len(subjs)):
                to_take[i] = int(left * to_take[i] / sum_weights)

            sum_weights = sum(to_take)
            to_take[0] += left - sum_weights

            for i, subj in enumerate(dict.fromkeys(subjs)):
                if to_take[i] == 0:
                    continue
                used = self._get_rel_map(subj, rel_map, depth=6, limit=to_take[i])
                if used < to_take[i]:
                    to_del[subj] = True
                    taken += used
            if taken == 0:
                break
            left -= taken
            subjs = list(filter(lambda s : s not in to_del, subjs))
                
        for key in rel_map:
            # print("lol", key)
            rel_map[key] = list(map(lambda t : [t[0], t[1], t[2]], list(set(map(lambda l : (l[0], l[1], l[2]), rel_map[key])))))
            # print(rel_map[key])
            
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
            for key in triple['readable']:
                self.add_auxilary_triples(triple['readable'][key], triple['processed'][key], graph)
            proc_triple = triple['processed']
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
        query = query.lstrip().rstrip()
        if (query.startswith("assistant: ```sparql")):
            query = query[len("assistant: ```sparql"):]
        if (query.startswith("```sparql")):
            query = query[len("```sparql"):]
        if (query.endswith("```")):
            query = query[:-len("```"):]
        query = query.lstrip().rstrip()
        print("HERE")
        print(query)
        self.sparql.method = 'GET'
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat('json')
        print(self.sparql.query().convert())
        print(self.sparql.query().convert()['results']['bindings'])
        print(self.sparql.query().convert()['results']['bindings'][0])
        print("EH")
        # print(self.sparql.query().convert()['results']['bindings'][0].keys()[0])
        # print("UUH")
        # print(self.sparql.query().convert()['results']['bindings'][0].values()[0])
        # print("AAH")
        res2 = list(map(lambda dict : list(map(lambda key:  (key, self.unURIfy(dict[key]['value'])), list(dict.keys()))), self.sparql.query().convert()['results']['bindings']))
        print("OUT")
        print(res2)
        return res2

    def unURIfy(self, uri):
        if self.random_uri in uri:
            res = unquote_plus(uri.replace(self.random_uri, ""))
            random_id = res.split()[-1]
            return res
        if self.value_uri in uri:
            return unquote_plus(uri.replace(self.value_uri, ""))
        if self.predicate_uri in uri:
            return unquote_plus(uri.replace(self.predicate_uri, ""))
        if self.frequent_predicate_uri in uri:
            return unquote_plus(uri.replace(self.frequent_predicate_uri, ""))