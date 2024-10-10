FROM python:3.13-slim AS builder

WORKDIR /usr/src/app

COPY setup.py /usr/src/app/
COPY README.md /usr/src/app/


RUN buildDeps='gcc libc6-dev make' \
    && set -x \
    && apt-get update && apt-get install -y $buildDeps --no-install-recommends \
    && pip install -e . \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove $buildDeps

COPY prometheus_mysql_exporter/*.py /usr/src/app/prometheus_mysql_exporter/
COPY LICENSE /usr/src/app/

FROM builder
EXPOSE 9207
ENTRYPOINT ["python", "-u", "/usr/local/bin/prometheus-mysql-exporter"]
