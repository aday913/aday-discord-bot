FROM python:3.11.7-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt

RUN pip3 install --upgrade pip

RUN pip3 install -r requirements.txt

RUN pip3 install yt-dlp

RUN apt-get update && apt-get install -y ffmpeg

COPY . .

CMD [ "python3", "main.py"]
