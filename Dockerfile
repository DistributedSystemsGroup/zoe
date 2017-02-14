FROM 192.168.12.2:5000/zoe-base:latest

MAINTAINER Quang-Nhat Hoang-Xuan <qhoangxuan@kpmg.com>

COPY . /opt/zoe

WORKDIR /opt/zoe

RUN echo 'admin,admin,admin' > /opt/zoe/zoepass.csv


