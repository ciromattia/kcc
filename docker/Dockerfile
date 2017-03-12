# acidweb/kcc
FROM debian:stretch
MAINTAINER Paweł Jastrzębski <pawelj@iosphe.re>

ADD ./Build /Build

RUN apt-get update && apt-get -y dist-upgrade
RUN apt-get -y install build-essential curl ruby ruby-dev libpng-dev libjpeg-dev python3 python3-dev python3-pyqt5
RUN curl https://bootstrap.pypa.io/get-pip.py | python3
RUN apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

CMD /Build
