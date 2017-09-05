from setuptools import setup, find_packages
import sys
import os

version = '0.1.1.5'

setup(name='qingzhenyun-wcs-upload',
      version=version,
      description="Qiingzhenyun WCS SDK",
      long_description="""\
Qingzhenyun WCS SDK""",
      classifiers=[],
      author='zzzhr',
      author_email='zzzhr@hotmail.com',
      url='https://github.com/zzzhr1990/qingzhenyun-wcs-upload',
      license='Apache',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          'requests>=2.18.1',
          'python-magic>=0.4.13',
          'six>=1.10.0',
          'Twisted>=17.5.0',
          'urllib3>=1.21.1'
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
