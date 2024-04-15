FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY init_db.py init_db.py

CMD ["tail", "-f", "/dev/null"]