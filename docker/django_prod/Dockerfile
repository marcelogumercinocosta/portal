FROM python:3.8

WORKDIR /app

RUN pwd

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./doc/requirements/requirements.txt /app/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt
RUN pip install gunicorn

COPY . /app

RUN apt-get update
RUN apt-get install -y locales locales-all
ENV LC_ALL pt_BR.UTF-8
ENV LANG pt_BR.UTF-8
ENV LANGUAGE pt_BR.UTF-8

