FROM python:3.14.3

ENV HOME=/test
WORKDIR ${HOME}
ENV PYTHONPATH=${HOME}/code

COPY . /test

RUN pip install --no-cache-dir -r requirements.txt
