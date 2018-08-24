FROM kbase/kb_python:python3

ARG DEVELOPMENT
ARG BUILD_DATE
ARG VCS_REF
ARG BRANCH=develop
ENV LANG C.UTF-8

COPY ./*requirements*.txt /app/
WORKDIR /app

# Install all the python dependencies
# Dependencies are listed in files with the format <package-manager>-requirements-<env>.txt
# If the "-<env>" part is not in the filename, then those requirements are installed in every env.
RUN pip install -r pip-requirements.txt && \
    if [ "$DEVELOPMENT" ]; then pip install -r pip-requirements-dev.txt; fi && \
    conda install --yes -c conda-forge --file conda-requirements.txt

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
