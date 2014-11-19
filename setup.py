from setuptools import setup

setup(name='vconnector',
      version='0.3.1',
      description='VMware vSphere Connector Module for Python',
      long_description=open('README.rst').read(),
      author='Marin Atanasov Nikolov',
      author_email='dnaeon@gmail.com',
      license='BSD',
      url='https://github.com/dnaeon/py-vconnector',
      download_url='https://github.com/dnaeon/py-vconnector/releases',
      packages=['vconnector'],
      package_dir={'': 'src'},
      scripts=[
        'src/vconnector-cli',
      ],
      install_requires=[
        'pyvmomi >= 5.5.0-2014.1.1',
        'docopt >= 0.6.2',
        'tabulate >= 0.7.3',  
      ]
)
