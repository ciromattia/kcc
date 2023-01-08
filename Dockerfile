FROM --platform=linux/amd64 python:3.11-slim-buster as compile-amd64
ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT
RUN echo "I'm building for $TARGETOS/$TARGETARCH/$TARGETVARIANT"


COPY requirements.txt /opt/kcc/
ENV PATH="/opt/venv/bin:$PATH"
RUN DEBIAN_FRONTEND=noninteractive apt-get update -y && apt-get -yq upgrade && \
    apt-get install -y libpng-dev libjpeg-dev p7zip-full unrar-free libgl1 python3-pyqt5 && \
    python -m pip install --upgrade pip && \
    python -m venv /opt/venv && \
    python -m pip install -r /opt/kcc/requirements.txt


######################################################################################

FROM --platform=linux/arm64 python:3.11-slim-buster as compile-arm64
ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT
RUN echo "I'm building for $TARGETOS/$TARGETARCH/$TARGETVARIANT"

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    LANGUAGE=en_US:en

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN set -x && \
    TEMP_PACKAGES=() && \
    KEPT_PACKAGES=() && \
    # Packages only required during build
    TEMP_PACKAGES+=(build-essential) && \
    TEMP_PACKAGES+=(cmake) && \
    TEMP_PACKAGES+=(libfreetype6-dev) && \
    TEMP_PACKAGES+=(libfontconfig1-dev) && \
    TEMP_PACKAGES+=(libpng-dev) && \
    TEMP_PACKAGES+=(libjpeg-dev) && \
    TEMP_PACKAGES+=(libssl-dev) && \
    TEMP_PACKAGES+=(libxft-dev) && \
    TEMP_PACKAGES+=(make) && \
    TEMP_PACKAGES+=(python3-dev) && \
    TEMP_PACKAGES+=(python3-setuptools) && \
    TEMP_PACKAGES+=(python3-wheel) && \
    # Packages kept in the image
    KEPT_PACKAGES+=(bash) && \
    KEPT_PACKAGES+=(ca-certificates) && \
    KEPT_PACKAGES+=(chrpath) && \
    KEPT_PACKAGES+=(locales) && \
    KEPT_PACKAGES+=(locales-all) && \
    KEPT_PACKAGES+=(libfreetype6) && \
    KEPT_PACKAGES+=(libfontconfig1) && \
    KEPT_PACKAGES+=(p7zip-full) && \
    KEPT_PACKAGES+=(python3) && \
    KEPT_PACKAGES+=(python3-pip) && \
    KEPT_PACKAGES+=(python-pyqt5) && \
    KEPT_PACKAGES+=(qt5-default) && \
    KEPT_PACKAGES+=(unrar-free) && \
    # Install packages
    DEBIAN_FRONTEND=noninteractive apt-get update -y && apt-get -yq upgrade && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ${KEPT_PACKAGES[@]} \
        ${TEMP_PACKAGES[@]} \
        && \
    # Install required python modules
    python -m pip install --upgrade pip && \
#    python -m pip install -r /opt/kcc/requirements.txt && \
    python -m venv /opt/venv && \
    python -m pip install --upgrade pillow python-slugify psutil raven mozjpeg-lossless-optimization


######################################################################################

FROM --platform=linux/arm/v7 python:3.11-slim-buster as compile-armv7
ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT
RUN echo "I'm building for $TARGETOS/$TARGETARCH/$TARGETVARIANT"

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    LANGUAGE=en_US:en

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN set -x && \
    TEMP_PACKAGES=() && \
    KEPT_PACKAGES=() && \
    # Packages only required during build
    TEMP_PACKAGES+=(build-essential) && \
    TEMP_PACKAGES+=(cmake) && \
    TEMP_PACKAGES+=(libffi-dev) && \
    TEMP_PACKAGES+=(libfreetype6-dev) && \
    TEMP_PACKAGES+=(libfontconfig1-dev) && \
    TEMP_PACKAGES+=(libpng-dev) && \
    TEMP_PACKAGES+=(libjpeg-dev) && \
    TEMP_PACKAGES+=(libssl-dev) && \
    TEMP_PACKAGES+=(libxft-dev) && \
    TEMP_PACKAGES+=(make) && \
    TEMP_PACKAGES+=(python3-dev) && \
    TEMP_PACKAGES+=(python3-setuptools) && \
    TEMP_PACKAGES+=(python3-wheel) && \
    # Packages kept in the image
    KEPT_PACKAGES+=(bash) && \
    KEPT_PACKAGES+=(ca-certificates) && \
    KEPT_PACKAGES+=(chrpath) && \
    KEPT_PACKAGES+=(locales) && \
    KEPT_PACKAGES+=(locales-all) && \
    KEPT_PACKAGES+=(libfreetype6) && \
    KEPT_PACKAGES+=(libfontconfig1) && \
    KEPT_PACKAGES+=(p7zip-full) && \
    KEPT_PACKAGES+=(python3) && \
    KEPT_PACKAGES+=(python3-pip) && \
    KEPT_PACKAGES+=(python-pyqt5) && \
    KEPT_PACKAGES+=(qt5-default) && \
    KEPT_PACKAGES+=(unrar-free) && \
    # Install packages
    DEBIAN_FRONTEND=noninteractive apt-get update -y && apt-get -yq upgrade && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ${KEPT_PACKAGES[@]} \
        ${TEMP_PACKAGES[@]} \
        && \
    # Install required python modules
    python -m pip install --upgrade pip && \
#    python -m pip install -r /opt/kcc/requirements.txt && \
    python -m venv /opt/venv && \
    python -m pip install --upgrade pillow python-slugify psutil raven mozjpeg-lossless-optimization


######################################################################################
FROM --platform=linux/amd64 python:3.11-slim-buster as build-amd64
COPY --from=compile-amd64 /opt/venv /opt/venv

FROM --platform=linux/arm64 python:3.11-slim-buster as build-arm64
COPY --from=compile-arm64 /opt/venv /opt/venv

FROM --platform=linux/arm/v7 python:3.11-slim-buster as build-armv7
COPY --from=compile-armv7 /opt/venv /opt/venv
######################################################################################

# Select final stage based on TARGETARCH ARG
FROM build-${TARGETARCH}${TARGETVARIANT}
LABEL com.kcc.name="Kindle Comic Converter"
LABEL com.kcc.author="Ciro Mattia Gonano and Paweł Jastrzębski"
LABEL org.opencontainers.image.description='Kindle Comic Converter'
LABEL org.opencontainers.image.documentation='https://github.com/darodi/kcc'
LABEL org.opencontainers.image.source='https://github.com/darodi/kcc'
LABEL org.opencontainers.image.authors='darodi'
LABEL org.opencontainers.image.url='https://github.com/darodi/kcc'
LABEL org.opencontainers.image.documentation='https://github.com/darodi/kcc'
LABEL org.opencontainers.image.vendor='darodi'
LABEL org.opencontainers.image.licenses='ISC'
LABEL org.opencontainers.image.title="Kindle Comic Converter"


ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
COPY . /opt/kcc
RUN DEBIAN_FRONTEND=noninteractive apt-get update -y && apt-get -yq upgrade && \
    apt-get install -y p7zip-full unrar-free  && \
    ln -s /app/kindlegen /bin/kindlegen && \
    cat /opt/kcc/kindlecomicconverter/__init__.py | grep version | awk '{print $3}' | sed "s/'//g" > /IMAGE_VERSION

ENTRYPOINT ["/opt/kcc/kcc-c2e.py"]
CMD ["-h"]