# This Dockerfile is used to build an image for testing Zoe with Jenkins and the Docker slave plugin

FROM ubuntu:trusty
MAINTAINER Daniele Venzano <venza@brownhat.org>

RUN locale-gen en_US.UTF-8 && \
    apt-get -q update && \
    DEBIAN_FRONTEND="noninteractive" apt-get -q upgrade -y --no-install-recommends && \
    DEBIAN_FRONTEND="noninteractive" apt-get -q install -y --no-install-recommends openssh-server openjdk-7-jre-headless python3 python3-pip git python3-dev build-essential libpq-dev  && \
    apt-get -q autoremove && \
    apt-get -q clean -y && rm -rf /var/lib/apt/lists/* && rm -f /var/cache/apt/*.bin && \
    sed -i 's|session    required     pam_loginuid.so|session    optional     pam_loginuid.so|g' /etc/pam.d/sshd && \
    mkdir -p /var/run/sshd

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Set user jenkins to the image
RUN useradd -m -d /home/jenkins -s /bin/sh jenkins && \
    echo "jenkins:jenkins" | chpasswd

RUN pip3 install --upgrade pip virtualenv

RUN printf "\nStrictHostKeyChecking no\n" >> /etc/ssh/ssh_config

# Standard SSH port
EXPOSE 22

# Default command
CMD ["/usr/sbin/sshd", "-D"]
