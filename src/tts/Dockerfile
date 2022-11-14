FROM python:3.10

COPY requirements.txt .

RUN pip install -r requirements.txt && \
    apt-get update -y && \
    apt-get install espeak -y

COPY app.py .

CMD ["python", "app.py"]
