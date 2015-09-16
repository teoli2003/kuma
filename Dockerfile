FROM ubuntu:14.04

RUN \
  sed -i 's/# \(.*multiverse$\)/\1/g' /etc/apt/sources.list \
  && apt-get update \
  && apt-get -y upgrade \
  && apt-get install -y \
    build-essential \
    curl \
    gettext \
    git \
    htop \
    libfreetype6 \
    libfreetype6-dev \
    libjpeg8 \
    libjpeg8-dev \
    libmemcached-dev \
    libmysqlclient-dev \
    libpng12-0 \
    libpng12-dev \
    libtidy-0.99-0 \
    libtidy-dev \
    libxml2-dev \
    libxslt1-dev \
    libxslt1.1 \
    make \
    man \
    mercurial \
    mysql-client \
    nodejs \
    nodejs-legacy \
    npm \
    python-pip \
    python-software-properties \
    python2.7 \
    python2.7-dev \
    rlwrap \
    ruby-dev \
    ruby-full \
    rubygems-integration \
    subversion \
    tmux \
    translate-toolkit \
    vim \
    wget \
  && rm -rf /var/lib/apt/lists/*

RUN pip install -U pip

COPY requirements /pip/requirements/
RUN cd /pip && \
    pip install --build ./build --cache-dir ./cache --no-deps \
    -r requirements/compiled.txt && \
    rm -r build cache

RUN npm install -g \
    fibers@1.0.1 \
    clean-css@2.2.16 \
    csslint@0.10.0 \
    jshint@2.7.0 \
    stylus@0.49.2 \
    uglify-js@2.4.13

RUN mkdir /code
WORKDIR /code
