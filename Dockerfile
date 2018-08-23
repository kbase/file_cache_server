FROM kbase/kb_python:latest

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
ENTRYPOINT [ "/kb/deployment/bin/dockerize" ]
CMD ["gunicorn", "--worker-class", "gevent", "--timeout", "1800", "--workers", "17", "-b", ":5000", "--reload", "app:app"]
