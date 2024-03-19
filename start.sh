docker network create network
docker run -p 7200:7200 --name graphdb --network network ontotext/graphdb:10.6.2
docker run --name server --network network server
docker run --env-file=.env -p 3000:3000 --name client --network network client