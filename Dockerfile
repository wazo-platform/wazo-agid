FROM python:2.7-slim-buster AS compile-image
LABEL maintainer="Wazo Maintainers <dev@wazo.community>"

RUN apt-get -qq update && apt-get -qq -y install python-virtualenv
RUN virtualenv /opt/venv
# Activate virtual env
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /usr/local/src/wazo-agid/requirements.txt
WORKDIR /usr/local/src/wazo-agid
RUN pip install -r requirements.txt

COPY setup.py /usr/local/src/wazo-agid/
COPY bin /usr/local/src/wazo-agid/bin
COPY wazo_agid /usr/local/src/wazo-agid/wazo_agid
RUN python setup.py install

FROM python:2.7-slim-buster AS build-image
COPY --from=compile-image /opt/venv /opt/venv

RUN apt-get -qq update && apt-get -qq -y install netcat-openbsd && apt-get -qq clean
HEALTHCHECK --interval=1s --retries=30 CMD nc -z -w1 localhost 4573

COPY ./etc/wazo-agid /etc/wazo-agid
RUN true\
    && adduser --disabled-password --gecos '' asterisk \
    && adduser --quiet --system --group --home /var/lib/wazo-agid wazo-agid \
    && mkdir -p /etc/wazo-agid/conf.d \
    && mkdir -p /etc/xivo \
    && install -D -o root -g root /dev/null /var/log/wazo-agid.log \
    && install -D -o root -g root /dev/null /etc/xivo/asterisk/xivo_ring.conf \
    && install -D -o root -g root /dev/null /etc/xivo/asterisk/xivo_fax.conf \
    && install -D -o root -g root /dev/null /etc/xivo/asterisk/xivo_in_callerid.conf

EXPOSE 4573

# Activate virtual env
ENV PATH="/opt/venv/bin:$PATH"
CMD ["wazo-agid"]
