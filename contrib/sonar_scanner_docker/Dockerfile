FROM java:alpine
ENV SONAR_SCANNER_VERSION 2.8

RUN apk add --no-cache wget && \
    wget https://sonarsource.bintray.com/Distribution/sonar-scanner-cli/sonar-scanner-${SONAR_SCANNER_VERSION}.zip && \
    unzip sonar-scanner-${SONAR_SCANNER_VERSION} && \
    cd /usr/bin && ln -s /sonar-scanner-${SONAR_SCANNER_VERSION}/bin/sonar-scanner sonar-scanner && \
    apk del wget

RUN apk add --no-cache python3 curl && rm -f /var/cache/apk/*
RUN curl https://bootstrap.pypa.io/get-pip.py | python3
RUN pip install pylint

COPY sonar-scanner-run.sh /usr/bin
RUN chmod 755 /usr/bin/sonar-scanner-run.sh
