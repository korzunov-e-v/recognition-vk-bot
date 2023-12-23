FROM reg.ocas.ai/dhub/library/python:3.10-slim AS dev

COPY pyproject.toml /srv
COPY poetry.lock /srv
WORKDIR /srv

RUN apt-get update && \
    pip install poetry==1.5.0 pip-autoremove && \
    poetry config virtualenvs.create false && \
    poetry install --no-cache --no-root && \
    apt autoremove -y

COPY src /srv/src
COPY .autoflake.cfg /srv
COPY .black /srv
COPY .flake8 /srv
COPY .isort.cfg /srv

EXPOSE 80
CMD python3 srv/src/srv.py
