# STAGE 1: BUILDER
# Contains all build tools and dev dependencies, will be discarded
FROM python:3.13-slim-bullseye AS builder

# Install system dependencies
RUN set -x && \
    BUILD_DEPS="build-essential cmake libffi-dev libfreetype6-dev libfontconfig1-dev libpng-dev libjpeg-dev libssl-dev libxft-dev make python3-dev python3-setuptools python3-wheel" && \
    RUNTIME_DEPS="bash ca-certificates chrpath locales locales-all libfreetype6 libfontconfig1 p7zip-full python3 python3-pip libgl1" && \
    DEBIAN_FRONTEND=noninteractive apt-get update -y && \
    apt-get install -y --no-install-recommends ${BUILD_DEPS} ${RUNTIME_DEPS}

RUN \
    set -x && \
    python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --upgrade pip

# Install numpy first, as it is unlikely to change and takes too long to compile
RUN \
    set -x && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir numpy==2.3.4

# Install PyMuPDF separately, as it is likely to change but still takes too long to compile
RUN \
    set -x && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir PyMuPDF==1.26.6

# Install Python dependencies using virtual environment
COPY requirements-docker.txt .

RUN \
    set -x && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir -r requirements-docker.txt

# STAGE 2: FINAL
# Clean, small and secure image with only runtime dependencies
FROM python:3.13-slim-bullseye

# Install runtime dependencies only
RUN \
    set -x && \
    DEBIAN_FRONTEND=noninteractive apt-get update -y && \
    apt-get install -y --no-install-recommends p7zip-full && \
    rm -rf /var/lib/apt/lists/*

# Copy artifacts from builder
COPY --from=builder /opt/venv /opt/venv
COPY . /opt/kcc/

WORKDIR /opt/kcc
ENV PATH="/opt/venv/bin:$PATH"

# Setup executable and version file
RUN \
    chmod +x /opt/kcc/entrypoint.sh && \
    ln -s /opt/kcc/kcc-c2e.py /usr/local/bin/c2e && \
    ln -s /opt/kcc/kcc-c2p.py /usr/local/bin/c2p && \
    ln -s /opt/kcc/entrypoint.sh /usr/local/bin/entrypoint && \
    cat /opt/kcc/kindlecomicconverter/__init__.py | grep version | awk '{print $3}' | sed "s/'//g" > /IMAGE_VERSION

LABEL com.kcc.name="Kindle Comic Converter" \
    com.kcc.author="Ciro Mattia Gonano, Paweł Jastrzębski and Darodi" \
    org.opencontainers.image.title="Kindle Comic Converter" \
    org.opencontainers.image.description='Kindle Comic Converter' \
    org.opencontainers.image.documentation='https://github.com/ciromattia/kcc' \
    org.opencontainers.image.source='https://github.com/ciromattia/kcc' \
    org.opencontainers.image.authors='Darodi and José Cerezo' \
    org.opencontainers.image.url='https://github.com/ciromattia/kcc' \
    org.opencontainers.image.vendor='ciromattia' \
    org.opencontainers.image.licenses='ISC'

ENTRYPOINT ["entrypoint"]
CMD ["-h"]
