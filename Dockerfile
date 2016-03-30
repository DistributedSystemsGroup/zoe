FROM python:3.4

MAINTAINER Daniele Venzano <venza@brownhat.org>

RUN mkdir -p /opt/zoe
WORKDIR /opt/zoe

COPY . /opt/zoe
RUN pip install --no-cache-dir -r requirements.txt

VOLUME /etc/zoe/

RUN python3 ./zoe-master.py --write-config /etc/zoe/zoe-master.conf
RUN python3 ./zoe-observer.py --write-config /etc/zoe/zoe-observer.conf
RUN python3 ./zoe-web.py --write-config /etc/zoe/zoe-web.conf
RUN python3 ./zoe-logger.py --write-config /etc/zoe/zoe-logger.conf

