xivo-agid
=========

[![Build Status](https://travis-ci.org/wazo-pbx/xivo-agid.png?branch=master)](https://travis-ci.org/wazo-pbx/xivo-agid)

xivo-agid is a server used by [XiVO](http://xivo.io) to serve [AGI](https://wiki.asterisk.org/wiki/pages/viewpage.action?pageId=32375589) requests coming from [Asterisk](http://asterisk.org).

Running unit tests
------------------

```
apt-get install libpq-dev python-dev libffi-dev libyaml-dev
pip install tox
tox --recreate -e py27
```
