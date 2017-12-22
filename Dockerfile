## Image to build from sources

FROM debian:stretch
MAINTAINER Wazo Maintainers <dev@wazo.community>

ENV DEBIAN_FRONTEND noninteractive
ENV HOME /root

# Add dependencies
RUN apt-get -qq update
RUN apt-get -qq -y install \
    git \
    apt-utils \
    python-pip \
    python-dev \
    libpq-dev \
    libyaml-dev \
    libsasl2-dev

# Install xivo-agid
WORKDIR /usr/src
ADD . /usr/src/agid
WORKDIR agid
RUN pip install -r requirements.txt
RUN python setup.py install

# Configure environment
RUN adduser --disabled-password --gecos '' asterisk
RUN touch /var/log/xivo-agid.log
RUN mkdir -p /etc/xivo-agid
RUN mkdir /var/lib/xivo-agid
RUN cp -a etc/xivo-agid/* /etc/xivo-agid/
WORKDIR /root

# Clean
RUN apt-get clean
RUN rm -rf /usr/src/agid

EXPOSE 4573

CMD ["xivo-agid", "-fd"]
