FROM python:3.9-alpine

RUN apk add --no-cache --virtual .build-deps gcc postgresql-dev musl-dev python3-dev
RUN apk add libpq

RUN pip install pipenv

COPY ./Pipfile ./Pipfile.lock ${PROJECT_DIR}/

RUN pipenv install --system --deploy --dev

RUN apk del --no-cache .build-deps

RUN mkdir -p /src
COPY app/ /src/
COPY tests/ /tests/

WORKDIR /src