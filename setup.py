import re
import ast

from setuptools import setup, find_packages

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('src/vconnector/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1))
    )

setup(name='vconnector',
      version=version,
      description='VMware vSphere Connector Module for Python',
      long_description=open('README.rst').read(),
      author='Marin Atanasov Nikolov',
      author_email='dnaeon@gmail.com',
      license='BSD',
      url='https://github.com/dnaeon/py-vconnector',
      download_url='https://github.com/dnaeon/py-vconnector/releases',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      scripts=[
        'src/vconnector-cli',
      ],
      install_requires=[
        'pyvmomi >= 6.0.0',
        'docopt >= 0.6.2',
        'tabulate >= 0.7.3',  
      ]
)
