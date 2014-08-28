from setuptools import setup

setup(name='vconnector',
      version='0.2.9',
      description='VMware vSphere Connector Module for Python',
      author='Marin Atanasov Nikolov',
      author_email='dnaeon@gmail.com',
      license='BSD',
      packages=['vconnector'],
      package_dir={'': 'src'},
      scripts=[
        'src/vconnector-cli',
      ],
      install_requires=[
        'pyvmomi >= 5.5.0',
        'docopt >= 0.6.1',
        'tabulate >= 0.7.2',  
      ]
)
