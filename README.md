# Knowledge Graph Generator and Querying

## Description

Client-Server application for constructing Knowledge Graphs through user input (most of the focus is on JSON format input and the hirearhic relations that come with it) and for answering user queries using an LLM with an overview of the constructed Knowledge Graph.

## Index

1. [Setup](#setup)
   - [GraphDB Setup](#GraphDB)
   - [Server Setup](#Server)
   - [Client Setup](#Client)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Contributing](#contributing)
6. [License](#license)

## Setup

### GraphDB

Simply run an instance (you can for example use a desktop app downloaded from https://www.ontotext.com/products/graphdb/download/) and take note of what host and port it is running on (by default 127.0.0.1:7200). You don't need to create repositories and indexes on your own as this can be done by the server part of the application, however if you make it and it already exists when the servers sees it, it will use yours.

### Server

in [kg-generator-server](./kg-generator-server/) run

```bash
pip3 install -r requirements.txt
```

to take care of Python dependencies. To run the server run

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
