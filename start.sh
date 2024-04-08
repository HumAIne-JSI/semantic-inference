docker network create network
# docker compose -f ./milvus2/docker-compose.yaml up
docker run -p 7200:7200 --name graphdb --network network ontotext/graphdb:10.6.2 &
docker run -p 3000:3000 --name client --network network client &
docker run -p 5000:5000 --name server --network network server &