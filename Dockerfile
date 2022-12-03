FROM python:3.8.6-slim-buster


# set working directory in container
WORKDIR /usr/src/app


RUN rm -f -r ./cache
RUN mkdir ./cache

RUN rm -f -r ./memoization_cache
RUN mkdir -p ./memoization_cache

# Copy and install packages
COPY requirements.txt /
RUN pip install --upgrade pip
RUN pip install -r /requirements.txt

# Copy app folder to app folder in container
COPY / /usr/src/app/

# Changing to non-root user
RUN useradd -m appUser
USER appUser

#EXPOSE 8090

# Run locally on port 8050
CMD gunicorn --bind 0.0.0.0:8095 app:server