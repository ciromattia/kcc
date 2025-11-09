FROM ghcr.io/ciromattia/kcc:base-latest

COPY . /opt/kcc/

# Setup executable and version file
RUN \
    chmod +x /opt/kcc/entrypoint.sh && \
    ln -s /opt/kcc/kcc-c2e.py /usr/local/bin/c2e && \
    ln -s /opt/kcc/kcc-c2p.py /usr/local/bin/c2p && \
    ln -s /opt/kcc/entrypoint.sh /usr/local/bin/entrypoint && \
    cat /opt/kcc/kindlecomicconverter/__init__.py | grep version | awk '{print $3}' | sed "s/'//g" > /IMAGE_VERSION

LABEL com.kcc.name="Kindle Comic Converter" \
    com.kcc.author="Ciro Mattia Gonano, Paweł Jastrzębski and Darodi" \
    org.opencontainers.image.description='Kindle Comic Converter' \
    org.opencontainers.image.source='https://github.com/ciromattia/kcc' \
    org.opencontainers.image.title="Kindle Comic Converter"

ENTRYPOINT ["entrypoint"]
CMD ["-h"]