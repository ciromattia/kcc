# Recipe used to build DEB package

FROM acidweb/kcc-base
MAINTAINER Paweł Jastrzębski <pawelj@iosphe.re>

ENV KCCVER 5.0
ADD . /app

RUN pip3 install pillow python-slugify psutil scandir pyinstaller
RUN gem install fpm
RUN useradd -ms /bin/bash kcc && chown -R kcc:kcc /app

USER kcc
WORKDIR /app
RUN pyinstaller -F -s --noupx kcc.py
RUN mkdir -p dist/usr/bin dist/usr/share/applications dist/usr/share/doc/kindlecomicconverter dist/usr/share/kindlecomicconverter dist/usr/share/lintian/overrides
RUN mv dist/kcc dist/usr/bin
RUN cp icons/comic2ebook.png dist/usr/share/kindlecomicconverter
RUN cp LICENSE.txt dist/usr/share/doc/kindlecomicconverter/copyright
RUN cp other/linux/kindlecomicconverter.desktop dist/usr/share/applications
RUN cp other/linux/kindlecomicconverter dist/usr/share/lintian/overrides

WORKDIR /app/dist
RUN fpm -f -s dir -t deb -n kindlecomicconverter -v $KCCVER -m "Paweł Jastrzębski <pawelj@iosphe.re>" --license "ISC" --description "Comic and Manga converter for e-book readers.\nThis app allows you to transform your PNG, JPG, GIF, CBZ, CBR and CB7 files\ninto EPUB or MOBI format e-books." --url "https://kcc.iosphe.re/" --deb-priority "optional" --vendor "" --category "graphics" -d "unrar | unrar-free" -d "p7zip-full" usr

CMD mkdir -p /out/dist && cp kindlecomicconverter_${KCCVER}_amd64.deb /out/dist
