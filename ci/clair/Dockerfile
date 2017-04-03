FROM golang:1.8-alpine

MAINTAINER Quang-Nhat Hoang-Xuan <hxquangnhat@gmail.com>

VOLUME /config
EXPOSE 6060 6061

ENV GOPATH /go

RUN apk add --no-cache git bzr rpm xz && \
    go get -v github.com/coreos/clair/cmd/clair && \
    go install -v github.com/coreos/clair/cmd/clair && \
    mv /go/bin/clair /clair && \
    go install -v github.com/coreos/clair/contrib/analyze-local-images && \
    mv /go/bin/analyze-local-images /bin/analyzer && \
    rm -rf /go /usr/local/go

RUN apk update && \
    apk add ca-certificates wget && \
    update-ca-certificates

RUN wget https://get.docker.com/builds/Linux/x86_64/docker-17.03.0-ce.tgz && \
    tar -xvf docker-17.03.0-ce.tgz && \
    mv docker/docker /bin && \
    rm -rf docker docker-17.03.0-ce.tgz

ENTRYPOINT ["/clair"]
