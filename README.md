## vConnector -- Python VMware vSphere Connector Module

*vConnector* module provides basic primitives for connecting and disconnecting from a vSphere host (e.g. ESXi and/or vCenter server instances).

The purpose of *vConnector* is to provide a simple module for integration into other projects such as vSphere Pollers.

## Requirements

* Python 2.7.x
* [pysphere](https://code.google.com/p/pysphere/)

## Contributions

*vConnector* is hosted on Github. Please contribute by reporting issues, suggesting features or by sending patches using pull requests.

If you like this project please also consider supporting development using [Gittip](https://www.gittip.com/dnaeon/). Thank you!

## Installation

In order to install *vConnector* simply execute the command below:

	# python setup.py install
	
## Applications using vConnector module

The [py-vpoller project](https://github.com/dnaeon/py-vpoller) implements a distributed system for polling of vSphere Object properties uses the *vConnector* module for managing the connections to vSphere hosts.

