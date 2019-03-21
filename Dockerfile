FROM python:3.7-slim

ARG DEVELOPMENT
ARG BUILD_DATE
ARG VCS_REF
ARG BRANCH=develop
ENV LANG C.UTF-8

# Dockerize installation
RUN apt-get update && apt-get install -y wget
ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

COPY ./dev-requirements.txt  ./requirements.txt /tmp/
WORKDIR /app

# Install all the python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    if [ "$DEVELOPMENT" ]; then pip install --no-cache-dir -r /tmp/dev-requirements.txt; fi

# Run the app
COPY . /app

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/kbase/CachingService.git" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.schema-version="1.0.0-rc1" \
      us.kbase.vcs-branch=$BRANCH \
      maintainer="Steve Chan sychan@lbl.gov"

EXPOSE 5000
ENTRYPOINT [ "/usr/local/bin/dockerize" ]
CMD ["sh", "scripts/start_server.sh"]
