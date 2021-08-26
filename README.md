# wazo-agid

[![Build Status](https://jenkins.wazo.community/buildStatus/icon?job=wazo-agid)](https://jenkins.wazo.community/job/wazo-agid)

wazo-agid is a server used by [Wazo](http://wazo.community) to serve
[AGI](https://wiki.asterisk.org/wiki/pages/viewpage.action?pageId=32375589) requests coming from
[Asterisk](http://asterisk.org).

The AGI protocol is documented in the [Asterisk wiki](https://wiki.asterisk.org/wiki/display/AST/Asterisk+18+AGI+Commands).

## Running unit tests

```bash
apt-get install libpq-dev python-dev libffi-dev libyaml-dev
pip install tox
tox --recreate -e py27
```

## Integration tests

To add feature to AGI mock server:

* On wazo host: `tcpdump -i lo -w /tmp/agi.pcap`
* Execute the real agi
* `scp <wazo>:/tmp/agi.pcap .`
* Open `agi.pcap` with Wireshark
* Apply filter `tcp.port == 4573`
