ARG PYTHON_VERSION=3.12-alpine
FROM python:$PYTHON_VERSION

RUN apk update && \
    apk upgrade && \
    apk add git g++ bash build-base linux-headers

RUN python -m pip install poetry

COPY ./Docker/start.sh /start.sh
RUN sed -i 's/\r$//g' /start.sh
RUN chmod +x /start.sh

ARG APP_HOME=/app
WORKDIR ${APP_HOME}

COPY poetry.lock /app/poetry.lock
COPY pyproject.toml /app/pyproject.toml

RUN poetry install --no-root

COPY . /app

ENTRYPOINT ["/start.sh"]