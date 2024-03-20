#!/bin/bash

source ./.env
cd chatgpt-retrieval-plugin
poetry env use python3.10
poetry run start &
cd ..
python3 ./app.py "$@"