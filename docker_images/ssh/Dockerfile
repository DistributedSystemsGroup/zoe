FROM ubuntu:14.04

MAINTAINER Daniele Venzano <venza@brownhat.org>

RUN apt-get update && apt-get install -y openssh-server openssh-client ldap-auth-client libnss-ldap sudo vim
RUN mkdir /var/run/sshd

COPY ldap.conf /etc/ldap.conf

RUN auth-client-config -t nss -p lac_ldap

#RUN pam-auth-update

RUN echo "session required        pam_mkhomedir.so skel=/etc/skel umask=0022" >> /etc/pam.d/common-session

RUN echo "bigfoot_admin ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

RUN locale-gen en_US.utf8

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]


