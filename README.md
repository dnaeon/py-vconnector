## vConnector -- VMware vSphere Connector Module for Python

`vConnector` is a wrapper module around [pyVmomi VMware vSphere bindings](https://github.com/vmware/pyvmomi),
which provides methods for connecting and retrieving of objects from a VMware vSphere server.

The purpose of `vConnector` is to provide the basic primitives for building more complex application.
`vConnector` can also be used for managing the user/pass/host credentials for your vSphere environment using an SQLite database,
which in turn can be shared between multiple applications requiring access to your vSphere environment through a common interface.

## Requirements

* Python 2.7.x
* [docopt](https://github.com/docopt/docopt)
* [pyVmomi](https://github.com/vmware/pyvmomi)
* [tabulate](https://pypi.python.org/pypi/tabulate)

## Contributions

*vConnector* is hosted on Github. Please contribute by reporting issues, suggesting features or by sending patches using pull requests.

## Installation

In order to install *vConnector* simply execute the command below:

	# python setup.py install
	
## Applications using vConnector module

* [vPoller - VMware vSphere Distributed Pollers written in Python](https://github.com/dnaeon/py-vpoller)

## Using the vConnector CLI tool

Using the `vconnector-cli` tool you can manage the user/pass/host credentials of your vSphere environment. The `vconnector-cli` tool
stores this information in an SQLite database, which also makes it easy to be shared between other applications.

First, initialize the `vConnector` database by executing the command below:

	$ vconnector-cli init

Here is how to add a new vSphere host to the `vConnector` database:

	$ vconnector-cli -H vc01.example.org -U root -P p4ssw0rd add

Here is how to update an already existing vSphere host from the `vConnector` database:

	$ vconnector-cli -H vc01.example.org -U root -P newp4ssw0rd update

Here is how to remove a vSphere host using `vconnector-cli`:

	$ vconnector-cli -H vc01.example.org remove

Here is how to enable a vSphere host using `vconnector-cli`:

	$ vconnector-cli -H vc01.example.org enable

Here this is how to disable a vSphere host:

	$ vconnector-cli -H vc01.example.org disable

And here is how to get the currently registered vSphere hosts from the `vConnector` database:

	$ vconnector-cli get
	+---------------------------+---------------------+--------------+-----------+
	| Hostname                  | Username            | Password     |   Enabled |
	+===========================+=====================+==============+===========+
	| vc01.example.org          | root                | p4ssw0rd     |         0 |
	+---------------------------+---------------------+--------------+-----------+

## Using the vConnector module

Here are a few examples of using the `vconnector` module.

Connecting to a vSphere host:

	>>> from vconnector.core import VConnector
	>>> client = VConnector(user='root', pwd='p4ssw0rd', host='vc01.example.org')
	>>> client.connect()

Disconnecting from a vSphere host:

	>>> client.disconnect()

Re-connecting to a vSphere host:

	>>> client.reconnect()

How to get a `VMware vSphere View` of all `VirtualMachine` managed objects:

	>>> from vconnector.core import VConnector
	>>> client = VConnector(user='root', pwd='p4ssw0rd', host='vc01.example.org')
	>>> client.connect()
	>>> vms = client.get_vm_view()
	>>> print vms.view

How to get a Managed Object by a specific property, e.g. find the Managed Object of an ESXi host which name is `esx01.example.org`:

	>>> import pyVmomi
	>>> from vconnector.core import VConnector
	>>> client = VConnector(user='root', pwd='p4ssw0rd', host='vc01.example.org')
	>>> client.connect()
	>>> host = client.get_object_by_property(property_name='name', property_value='esxi01.example.org', obj_type=pyVmomi.vim.HostSystem)
	>>> print host.name
	esxi01.example.org
	>>> client.disconnect()

How to collect properties for Managed Objects, e.g. get the `name` and `capacity` properties for all `Datastore` managed objects:

	>>> import pyVmomi
	>>> from vconnector.core import VConnector
	>>> client = VConnector(user='root', pwd='p4ssw0rd', host='vc01.example.org')
	>>> client.connect()
	>>> datastores = client.get_datastore_view()
	>>> result = client.collect_properties(view_ref=datastores, obj_type=pyVmomi.vim.Datastore, path_set=['name', 'info.capacity'])
	>>> print result
	>>> client.disconnect()

