from distutils.core import setup

setup(
    name='Juju Charm Toolkit',
    version='0.1.0',
    author='Justin SB',
    author_email='justin@fathomdb.com',
    packages=['jujucharmtoolkit'],
    url='http://pypi.python.org/pypi/JujuCharmToolkit/',
    license='LICENSE.txt',
    description='Helper functions for creating Juju Charms.',
    long_description=open('README.md').read(),
    install_requires=[
    ],
)