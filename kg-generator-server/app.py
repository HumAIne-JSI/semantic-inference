import requests
import json
from flask import Flask, jsonify, request
from flask_cors import CORS

import argparse
import sys
from waitress import serve

from GraphDBStore import GraphDBStore
from llm import get_query_engine, get_chat_engine, query_engine_query
from datetime import datetime

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# log_file = open("app.log","w")
# sys.stdout = log_file


app = Flask(__name__)
CORS(app)

graph_store = None
query_engine = None

@app.route('/api/data')
def get_data():
    data = {'message': 'Hello from the backend!'}
    return jsonify(data)

@app.route('/get-triples-from-json', methods=['POST'])
def get_triples_from_json():
    try:
        input_string = request.json.get('json_string')
        # print(input_string)
        json_object = json.loads(input_string)
        triples = []
        # graph_store.generate_triples_from_json("JSON root", json_object, triples)
        graph_store.generate_triples_from_AAS_json(json_object, triples)
        return jsonify({'triples': triples})

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 400
    
@app.route('/commit-triples', methods=['POST'])
def commit_triples():
    try:
        input_triples = request.json.get('triples')
        print("commiting")
        graph_store._upsert_triples(input_triples)
        print("commited", len(input_triples))
        return jsonify({})

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 400
    

import re

def remove_words_with_substring(input_string, substring):
    # Remove words containing the specified substring
    words = input_string.split()
    filtered_words = [word for word in words if substring not in word]
    filtered_string = ' '.join(filtered_words)

    # Remove double spaces
    cleaned_string = re.sub(' +', ' ', filtered_string)

    return cleaned_string

@app.route('/query', methods=['POST'])
def query():
    try:
        input_string = request.json.get('query')
        breadth = request.json.get('breadth')
        scope = request.json.get('scope')
        score_weight = request.json.get('score_weight')
        llmModel = request.json.get("llmModel")
        useQueryGeneration = request.json.get("useQueryGeneration")
        print("input:", input_string, "breadth:", breadth, "scope:", scope, "score weight:", score_weight)
        graph_store.width = breadth
        graph_store.quantity = scope
        graph_store.score_weight = score_weight
        print(llmModel, useQueryGeneration)
        # answer = get_query_engine(graph_store, llmModel).query(input_string)
        answer = query_engine_query(input_string, graph_store, llmModel, useQueryGeneration)
        print(answer.response, type(answer.response))
        print("WTF")
        return jsonify({'answer': answer.response})

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 400



def setup_graphDB_repo(graphDBhost, graphDBport, graphDBrepository, graphDBgraph, hostFromOutside):

    url = f"http://{graphDBhost}:{graphDBport}/repositories/{graphDBrepository}"
    print(url)
    rest_url = f"http://{graphDBhost}:{graphDBport}/rest/repositories/"
    headers = {'Accept': 'application/json'}
    session = requests.Session()
    retry = Retry(connect=6, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    response = session.get(url, headers=headers)
    print(response.status_code, response.text)
    if (response.status_code == 404):
        # create repo

        file_content = open('Knowledge-Graph-Test-config.ttl', 'r').read()
        response = requests.post(rest_url, files={'config': ('Knowledge-Graph-Test-config.ttl', file_content.replace('Knowledge-Graph-Test', graphDBrepository).encode())})
        print(response.status_code, response.text)
    response = requests.get(url, headers=headers)
    print(response.status_code, response.text)
    
    global graph_store
    graph_store = GraphDBStore(
        url,
        graphDBgraph
    )
    # query = f"""
    # PREFIX : <http://www.ontotext.com/connectors/lucene#>
    # PREFIX inst: <http://www.ontotext.com/connectors/lucene/instance#>

    # INSERT DATA {{
    # inst:search :createConnector '''
    #     {{
    #     "fields": [
    #         {{
    #         "fieldName": "search",
    #         "propertyChain": [
    #             "http://www.w3.org/2000/01/rdf-schema#label"
    #         ],
    #         "indexed": true,
    #         "stored": true,
    #         "analyzed": true,
    #         "multivalued": true,
    #         "ignoreInvalidValues": false,
    #         "facet": true
    #         }}
    #     ],
    #     "languages": [],
    #     "types": [
    #         "{graphDBgraph}"
    #     ],
    #     "readonly": false,
    #     "detectFields": false,
    #     "importGraph": false,
    #     "skipInitialIndexing": false,
    #     "boostProperties": [],
    #     "stripMarkup": false
    #     }}
    # ''' .
    # }}
    # """
    # print(query)
    
    query = f"""
        PREFIX :<http://www.ontotext.com/connectors/retrieval#>
        PREFIX inst:<http://www.ontotext.com/connectors/retrieval/instance#>
        INSERT DATA {{
            inst:gpt-search :createConnector '''
        {{
        "fields": [
            {{
            "fieldName": "gpt-search",
            "propertyChain": [
                "http://www.w3.org/2000/01/rdf-schema#label"
            ],
            "indexed": true,
            "multivalued": true,
            "fieldTextPrefix": "has {{}}",
            "objectFields": []
            }}
        ],
        "languages": [],
        "types": [
            "{graphDBgraph}"
        ],
        "readonly": false,
        "detectFields": false,
        "importGraph": false,
        "skipInitialIndexing": false,
        "retrievalUrl": "http://{hostFromOutside}:8000",
        "retrievalBearerToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        "bulkUpdateBatchSize": 1000
        }}
        ''' .
        }}
        """


    print(query)

    try:
        import SPARQLWrapper
        sparql = SPARQLWrapper.SPARQLWrapper(url + "/statements")
        sparql.method = 'POST'
        sparql.setQuery(query)
        sparql.query()
    except Exception as e:
        print("Connector already exists")
    global query_engine
    # query_engine = get_query_engine(graph_store)
    # global chat_engine
    # chat_engine = get_chat_engine(query_engine)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Hostname or IP address (default: 0.0.0.0)')
    parser.add_argument('--hostFromOutside', type=str, default='server', help='What hostname graphdb uses to connect to this server')
    parser.add_argument('--port', type=int, default=5000, help='Port number (default: 5000)')
    parser.add_argument('--debug', type=bool, default=False, help='Run in debug mode (Flask)?')
    parser.add_argument('--graphDBhost', type=str, default='graphdb', help='graphDB host')
    parser.add_argument('--graphDBport', type=str, default=7200, help='graphDB port')
    parser.add_argument('--graphDBrepository', type=str, default='Knowledge-Graph', help='graphDB repository name')
    parser.add_argument('--graphDBgraph', type=str, default='http://knowledge-graph.com', help='graphDB graph name')
    args = parser.parse_args()
    print(args.graphDBhost)
    setup_graphDB_repo(args.graphDBhost, args.graphDBport, args.graphDBrepository, args.graphDBgraph, args.hostFromOutside)
    if "--debug" in sys.argv:
        app.run(debug=True, host=args.host, port=args.port)
    else:
        serve(app, host=args.host, port=args.port)