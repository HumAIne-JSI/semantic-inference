docker network create network
bash ./milvus2/standalone_embed_latest.sh start
docker run -p 5002:7200 --name graphdb --network network ontotext/graphdb:10.6.2 &
docker run -p 5001:3000 --name client --network network client &
docker run -p 5003:5000 -p 5004:8000 --name server --network network server &