FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Tools.py QandA.py DataLoader.py Json_RPC_Plumbing.py MethodHandlers.py ./
COPY data/ ./data/
COPY Server/ServerHTTP.py ./

ENV PORT=8080
EXPOSE 8080
CMD ["python", "ServerHTTP.py"]