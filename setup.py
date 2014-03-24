from setuptools import setup

setup(name='py-vconnector',
      version='0.1.0',
      description='Python VMware vSphere Connector',
      author='Marin Atanasov Nikolov',
      author_email='dnaeon@gmail.com',
      license='BSD',
      packages=['vconnector'],
      package_dir={'': 'src'},
      install_requires=[
        'pyvmomi >= 5.5.0',
      ]
)
