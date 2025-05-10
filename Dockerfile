FROM python:3.11-slim

RUN apt-get update && apt-get install -y gcc git

WORKDIR /app
RUN git clone https://github.com/olachinkei/wandb-fc-translation-agent.git . && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
