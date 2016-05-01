# acidweb/kcc
FROM debian:jessie
MAINTAINER Paweł Jastrzębski <pawelj@iosphe.re>

ADD ./Build /Build

RUN printf "deb http://httpredir.debian.org/debian stretch main" > /etc/apt/sources.list.d/stretch.list
RUN printf "Package: *\nPin: release a=testing\nPin-Priority: 400\n" > /etc/apt/preferences.d/stretch.pref
RUN printf "deb http://httpredir.debian.org/debian sid main" > /etc/apt/sources.list.d/sid.list
RUN printf "Package: *\nPin: release a=testing\nPin-Priority: 300\n" > /etc/apt/preferences.d/sid.pref
RUN apt-get update && apt-get -y dist-upgrade
RUN apt-get -y install build-essential curl ruby ruby-dev libpng-dev libjpeg-dev
RUN apt-get -y -t testing install python3 python3-dev
RUN apt-get -y -t unstable install python3-pyqt5
RUN curl https://bootstrap.pypa.io/get-pip.py | python3
RUN apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

CMD /Build
