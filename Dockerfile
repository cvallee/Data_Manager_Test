FROM python:3.14.3

ENV PYTHONPATH=/test
ENV HOME=/test
WORKDIR ${HOME}

COPY . /test

RUN pip install --no-cache-dir -r requirements.txt
