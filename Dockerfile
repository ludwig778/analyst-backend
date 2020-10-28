FROM python:3.8-slim-buster AS base

RUN mkdir -p /usr/share/man/man1 && \
    mkdir -p /usr/share/man/man7 && \
    apt update && \
    apt install -y make postgresql-client && \
    rm -rf /var/lib/apt/lists/*

RUN ["adduser", "--gecos", "", "--disabled-password", "analyst"]
USER analyst

ENV PATH=/usr/local/bin:/usr/bin:/home/analyst/.local/bin:/bin
ENV PYTHONPATH=/home/analyst/analyst

COPY requirements.txt /tmp/
RUN python3 -m pip install --no-cache-dir --user \
    --requirement /tmp/requirements.txt

RUN mkdir /home/analyst/analyst
WORKDIR /home/analyst/analyst
COPY --chown=analyst:analyst . .

ENTRYPOINT ["make"]
CMD ["run_dev"]

FROM base as dev
COPY requirements.dev.txt /tmp/
RUN python3 -m pip install --no-cache-dir --user \
    --requirement /tmp/requirements.dev.txt
