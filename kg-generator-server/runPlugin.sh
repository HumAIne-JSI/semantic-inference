#!/bin/bash

source ./.env
cd chatgpt-retrieval-plugin
poetry env use python3.10
poetry shell
poetry install
# poetry run start &
cd ..