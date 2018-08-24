FROM kbase/kb_python:python3

ARG BUILD_DATE
ARG VCS_REF
ARG BRANCH=develop
ENV LANG C.UTF-8

COPY requirements.txt /app/requirements.txt
COPY dev-requirements.txt /app/dev-requirements.txt
WORKDIR /app

# Unfortunately conda doesn't have the minio python clients
# so break that out of the requirements, and install that with
# pip and install the rest using conda
RUN MINIO=`grep minio requirements.txt` && \
    pip install $MINIO && \
    grep >requirements.conda -v $MINIO requirements.txt && \
    conda install --yes -c conda-forge --file requirements.conda

# Run the app
COPY . /app

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/kbase/CachingService.git" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.schema-version="1.0.0-rc1" \
      us.kbase.vcs-branch=$BRANCH \
      maintainer="Steve Chan sychan@lbl.gov"

ENTRYPOINT [ "/kb/deployment/bin/dockerize" ]
CMD ["gunicorn", "--worker-class", "gevent", "--timeout", "1800", "--workers", "17", "-b", ":5000", "--reload", "app:app"]
