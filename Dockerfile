FROM python:3.10.12-slim

WORKDIR /web

COPY ./requirements.txt /web/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /web/requirements.txt

COPY ./app /web/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
