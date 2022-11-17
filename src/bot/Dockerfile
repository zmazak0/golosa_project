FROM python:3.10

ENV PROJECT_ROOT /bot
COPY . $PROJECT_ROOT
WORKDIR $PROJECT_ROOT

RUN pip install -r requirements.txt

CMD ["python", "app.py"]
