FROM python:3.4

MAINTAINER Daniele Venzano <venza@brownhat.org>

RUN mkdir -p /opt/zoe
WORKDIR /opt/zoe

COPY ./requirements* /opt/zoe/

RUN pip install -U pip setuptools
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements_tests.txt

COPY . /opt/zoe

RUN echo 'admin,admin,admin' > /opt/zoe/zoepass.csv
