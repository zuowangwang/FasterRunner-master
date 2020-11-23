FROM ubuntu:16.04

ENV LANG C.UTF-8
ENV TZ=Asia/Shanghai
# Install required packages and remove the apt packages cache when done.

RUN sed -i s@/archive.ubuntu.com/@/mirrors.aliyun.com/@g /etc/apt/sources.list && \
    apt-get clean && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
    python3 \
    python3-dev \
    python3-setuptools \
    python3-pip \
    libmysqlclient-dev \
    nginx \
    python3-dateutil \
    tzdata && \
    dpkg-reconfigure --frontend noninteractive tzdata

WORKDIR /opt/workspace/FasterRunner/

COPY start.sh .
COPY manage.py .
COPY uwsgi.ini .
COPY requirements.txt .

RUN  pip3 install -r ./requirements.txt -i \
     https://pypi.douban.com/simple \
     --default-timeout=100

EXPOSE 5000

CMD bash ./start.sh


