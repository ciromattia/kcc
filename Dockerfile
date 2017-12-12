FROM python:3
MAINTAINER Michel Saoula <dev@saoula.com>
LABEL com.kcc.name="Kindle Comic Converter"
LABEL com.kcc.author="Ciro Mattia Gonano and Paweł Jastrzębski"

ARG KINDLEGEN_URL=http://kindlegen.s3.amazonaws.com/kindlegen_linux_2.6_i386_v2_9.tar.gz

RUN apt-get update && apt-get install -y libpng-dev libjpeg-dev p7zip-full unrar-free
RUN wget $KINDLEGEN_URL -O - | tar -xzf - -C /usr/bin kindlegen

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /root

WORKDIR /app

ENTRYPOINT ["/root/kcc-c2e.py"]
CMD ["-h"]