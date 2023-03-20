FROM ubuntu:22.04
RUN apt-get update; apt-get install -y python3-pip
RUN mkdir /home/cs640
WORKDIR /home/cs640
RUN mkdir /home/cs640/logs
COPY *.txt /home/cs640

CMD ["sh", "/home/cs640/start.sh"]