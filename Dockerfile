FROM mtgupf/essentia:stretch-python3
ENV PYTHONUNBUFFERED 1
ENV LANG C.UTF-8

RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

RUN wget -O /usr/local/bin/dumb-init https://github.com/Yelp/dumb-init/releases/download/v1.2.0/dumb-init_1.2.0_amd64 \
    && chmod +x /usr/local/bin/dumb-init

RUN wget -q -O - https://deb.nodesource.com/setup_8.x | bash - \
      && apt-get install -y --no-install-recommends \
         cmake \
         libmad0-dev \
         libsndfile1-dev \
         libgd2-xpm-dev \
         libboost-filesystem-dev \
         libboost-program-options-dev \
         libboost-regex-dev \
         nodejs \
         python3-pip \
         python3-setuptools \
         libsndfile1-dev \
         build-essential \
         libpython3.5-dev \
         lame \
      && rm -rf /var/lib/apt/lists/*


RUN mkdir /code
WORKDIR /code

RUN pip3 install --no-cache-dir -i https://mtg-devpi.sb.upf.edu/asplab/dev/ numpy==1.15.2
ADD requirements /code/
RUN pip3 install --no-cache-dir -i https://mtg-devpi.sb.upf.edu/asplab/dev/ -r requirements

ADD requirements_dev /code/
RUN pip3 install --no-cache-dir -i https://mtg-devpi.sb.upf.edu/asplab/dev/ -r requirements_dev

RUN mkdir /sources
WORKDIR /sources
RUN git clone https://github.com/MTG/pycompmusic.git
WORKDIR /sources/pycompmusic
RUN pip3 install -e .


ADD package.json /code/
WORKDIR /code
RUN npm install

ADD . /code/

RUN npm run build
WORKDIR /code
# TODO: Could be made part of the frontend build script
RUN bash build-less.sh

