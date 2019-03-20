from setuptools import setup, find_packages
from setuptools import distutils
import os
import versioneer


def get_version():
    if os.path.exists("PKG-INFO"):
        metadata = distutils.dist.DistributionMetadata("PKG-INFO")
        return metadata.version
    else:
        return versioneer.get_version()


setup(name='datalake-dtkav',
      url='https://github.com/dtkav/datalake',
      version=get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='datalake-dtkav: a fork of planetlabs/datalake',
      author='Daniel Grossmann-Kavanagh, Brian Cavagnolo',
      author_email='me@danielgk.com',
      packages=find_packages(exclude=['test']),
      install_requires=[
          'boto>=2.38.0',
          'memoized_property>=1.0.1',
          'simplejson>=3.3.1',
          'pyblake2>=0.9.3',
          'click>=4.1',
          'datalake-common-dtkav>=0.28',
          'python-dotenv>=0.1.3',
          'requests>=2.5',
          'six>=1.10.0',
          'py-multibase>=1.0.1',
          'py-multihash>=0.2.3',
      ],
      extras_require={
          'test': [
              'pytest==3.0.2',
              'moto==0.4.27',
              'twine==1.5.0',
              'pip==7.1.0',
              'wheel==0.24.0',
              'flake8==2.5.0',
              'responses==0.5.0',
              'pytz>=2015.4',
          ],
          # the queuable feature allows users to offload their datalake pushes
          # to a separate uploader process.
          'queuable': [
              'pyinotify>=0.9.4',
          ],
          'sentry': [
              'raven>=5.0.0',
          ],
          'krb': [
            'requests-kerberos>=0.10.0',
          ]
      },
      classifiers=[
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.5',
      ],
      entry_points="""
      [console_scripts]
      datalake=datalake.scripts.cli:cli
      """)
