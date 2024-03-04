docker build -t fastapi-crypto-exchanges .
docker run -p 8000:80 --name fastapi fastapi-crypto-exchanges
