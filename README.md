# Knowledge Graph Generator and Querying

## Description

Client-Server application for constructing Knowledge Graphs through user input (most of the focus is on JSON format input and the hirearhic relations that come with it) and for answering user queries using an LLM with an overview of the constructed Knowledge Graph.

## Index

1. [Docker Setup](#docker-setup)
2. [Setup](#setup)
   - [GraphDB Setup](#GraphDB)
   - [Server Setup](#Server)
   - [Client Setup](#Client)
3. [Llama_index](#Llama_index)

## Docker setup

## Non-docker setup (still makes sense, however some defaults might have changed to make more sense for docker)

### GraphDB

Simply run an instance (you can for example use a desktop app downloaded from https://www.ontotext.com/products/graphdb/download/) and take note of what host and port it is running on (by default 127.0.0.1:7200). You don't need to create repositories and indexes on your own as this can be done by the server part of the application, however if you make it and it already exists when the servers sees it, it will use yours.

### Server

in [kg-generator-server](./kg-generator-server/) run:

```bash
pip3 install -r requirements.txt
```

to take care of Python dependencies. To enable queries using GPT-3.5 Turbo paste your OpenAI key to an .env file located in the server directory, it's content should look like:

```
OPENAI_API_KEY=sk-...F63V
```

To run the server run

```bash
python3 ./app.py --host 127.0.0.1 --port 5000 --debug 0 --graphDBhost 127.0.0.1 --graphDBport 7200 --graphDBrepository Knowledge-Graph --graphDBgraph http://knowledge-graph.com
```

The following runs the server on the specified host and port and it connects to a graphDB server on the specified host and port. If debug is set to 0 then the server is run in a production setting (waitress package), otherwise in a debug environment (Flask). If the graphDBrepository with that name does not exist yet, it is created and along with it a Lucene search connector is created on it to be later used for querrying. graphDBgraph should be an URI, it tells in what subdivision of the repository the triples are written into / read from. The specified values in the above command call are all default values so running

```bash
python3 ./app.py
```

would have the same effect.

### Client

In [kg-generator-client](./kg-generator-client/) run

```bash
npm install
```

to install dependencies. To run client in development mode do

```bash
REACT_APP_SERVER_HOST=127.0.0.1 REACT_APP_SERVER_PORT=5000 npm run start
```

which is (by default) same as

```bash
npm run start
```

and to run it in production mode do:

```bash
REACT_APP_SERVER_HOST=127.0.0.1 REACT_APP_SERVER_PORT=5000 npm run build
npx serve -s build
```

or

```bash
npm run build
npx serve -s build
```

## Features

### Llama_index for making queries on the KG

LlamaIndex (https://www.llamaindex.ai/) is a data framework for connecting different data sources to large language models. It can be used for RAG (retrieval-augmented generation) applications (such as this one).

Benefits of RAG (getting information from data sources and adding it to LLM question context) over traditional LLM fine-tuning are

- RAG is cheaper,
- because of the cost of LLM training RAGs are easier to update with latest information,
- and source of LLM answers is more easily identified.

RAG pipeline
![1707828394202](https://docs.llamaindex.ai/en/stable/_images/basic_rag.png)

Llama_index can be used to index raw data by generating vector embeddings and storing them in a specialized database called a "vector store". It also supports generating and querying knowledge graphs, in our case we generated triplets from JSON and stored them in GraphDB without LLM help, but we used Llama_index to read from GraphDB and use the information to answer queries.
