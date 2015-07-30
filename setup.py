from setuptools import setup
from setuptools import distutils
from pip.req import parse_requirements
from pip.download import PipSession
import os
import sys

def get_version_from_pkg_info():
    metadata = distutils.dist.DistributionMetadata("PKG-INFO")
    return metadata.version

def get_version_from_pyver():
    try:
        import pyver
    except ImportError:
        if 'sdist' in sys.argv or 'bdist_wheel' in sys.argv:
            raise ImportError('You must install pyver to create a package')
        else:
            return 'noversion'
    version, version_info = pyver.get_version(pkg="datalake", public=True)
    return version

def get_version():
    if os.path.exists("PKG-INFO"):
        return get_version_from_pkg_info()
    else:
        return get_version_from_pyver()

setup(name='datalake',
      url='https://github.com/planetlabs/datalake',
      version=get_version(),
      description='datalake: a metadata-aware archive',
      author='Brian Cavagnolo',
      author_email='brian@planet.com',
      packages=['datalake'],
      install_requires=[
          'python-dateutil>=2.4.2',
          'pytz>=2015.4',
          'pyver>=1.0.18',
          'ConfigArgParse>=0.9.3',
          'boto>=2.38.0',
          'memoized_property>=1.0.2',
          'simplejson>=3.7',
      ],
      extras_require={
          'test': [
              'pytest==2.7.2',
              'moto==0.4.2',
              'twine==1.5.0',
              'pip==7.1.0',
              'wheel==0.24.0',
          ]
      },
      scripts=['bin/datalake'],
     )
