FROM python:3.11-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 只复制必要的文件，不再复制 config.json
COPY bot.py .

RUN mkdir -p logs

CMD ["python", "bot.py"]
