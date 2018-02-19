xivo-agid
=========

[![Build Status](https://jenkins.wazo.community/buildStatus/icon?job=xivo-agid)](https://jenkins.wazo.community/job/xivo-agid)

xivo-agid is a server used by [Wazo](http://wazo.community) to serve [AGI](https://wiki.asterisk.org/wiki/pages/viewpage.action?pageId=32375589) requests coming from [Asterisk](http://asterisk.org).

Running unit tests
------------------

```
apt-get install libpq-dev python-dev libffi-dev libyaml-dev
pip install tox
tox --recreate -e py27
```
