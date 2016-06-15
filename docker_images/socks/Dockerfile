FROM alpine:3.3

MAINTAINER Daniele Venzano <venza@brownhat.org>

#RUN apk add --update-cache openssh openssh-client

#ADD start-ssh.sh

#RUN adduser -D -h /home/user -s /bin/ash user
#RUN passwd -u user

RUN apk add --update-cache --repository http://dl-3.alpinelinux.org/alpine/edge/testing/ --allow-untrusted dante-server && rm -Rf /var/cache/apk/*

ADD sockd.conf /etc/sockd.conf

ENV CFGFILE /etc/sockd.conf
ENV PIDFILE /tmp/sockd.pid
ENV WORKERS 4

EXPOSE 1080

#CMD sh /start-ssh.sh

CMD sockd -f $CFGFILE -p $PIDFILE -N $WORKERS

