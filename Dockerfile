FROM python:3.12-slim

COPY ./src /home/core/

RUN apt-get update && apt-get install -y curl git && \
    groupadd --gid 2000 core && \
    useradd --uid 2000 --gid core \
            --home /home/core \
            --create-home \
            --shell /bin/bash core && \
    pip install flask \
                requests \
                waitress \
                python-dotenv \ 
                ollama && \
    chown core:core -R /home/core

RUN pip install git+https://github.com/amplec/utils
    
WORKDIR /home/core

USER core:core

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 CMD curl --fail http://localhost:5000/health || exit 1

CMD waitress-serve --port=5000 app:app
