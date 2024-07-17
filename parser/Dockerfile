FROM python:3.11.7-slim-bullseye

WORKDIR /parser

COPY requirements.txt .
RUN pip install -r requirements.txt


COPY . .


CMD ["./start.sh"]