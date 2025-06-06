# Backend\
# FROM postgres:17.5

# ENV POSTGRES_USER=postgres
# #ENV POSTGRES_PASSWORD=root
# ARG DB_PASSWORD
# ENV DB_PASSWORD=${DB_PASSWORD}
# ENV POSTGRES_DB=example

# docker build -t mydb:dev .

FROM php:8.2.12

RUN apt-get update && apt-get install -y \
    iputils-ping