# backend/Dockerfile
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ARG APP_USER=appuser
ARG APP_UID=1000
ARG APP_GID=1000

RUN groupadd -g ${APP_GID} ${APP_USER} && \
    useradd -u ${APP_UID} -g ${APP_USER} -d /app -s /bin/sh ${APP_USER} && \
    mkdir -p /app && \
    chown ${APP_USER}:${APP_USER} /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/
RUN chown -R ${APP_USER}:${APP_USER} /app

USER ${APP_USER}

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
