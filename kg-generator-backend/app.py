import json
from flask import Flask, jsonify, request
from flask_cors import CORS
import random
from urllib.parse import quote_plus, unquote_plus

from llama_index.graph_stores.types import GraphStore
from typing import Any, Dict, List, Optional, Protocol, TypedDict, runtime_checkable
from rdflib import Graph, URIRef, Literal, ConjunctiveGraph
from urllib.parse import quote_plus, unquote_plus
import re
import queue

from GraphDBStore import GraphDBStore
from llm import get_query_engine


    
graph_store = GraphDBStore(
    "http://domen-IdeaPad-Flex-5-14ARE05:7200/repositories/Knowledge-Graph-Test",
    "http://plooto.ga.com"
)   


query_engine = get_query_engine(graph_store)





app = Flask(__name__)
CORS(app)

@app.route('/api/data')
def get_data():
    data = {'message': 'Hello from the backend!'}
    return jsonify(data)

@app.route('/get-triples-from-json', methods=['POST'])
def get_triples_from_json():
    try:
        input_string = request.json.get('json_string')

        json_object = json.loads(input_string)
        triples = []
        graph_store.generate_triples_from_json("JSON root", json_object, triples)
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
        print("commited", len(input_triples), input_triples[0])
        return jsonify({})

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 400
    
@app.route('/query', methods=['POST'])
def query():
    try:
        input_string = request.json.get('query')
        print(input_string)
        answer = query_engine.query(input_string)
        print(answer.response, type(answer.response))
        return jsonify({'answer': answer.response})

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)