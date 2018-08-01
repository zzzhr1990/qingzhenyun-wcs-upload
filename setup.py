from setuptools import setup, find_packages
import sys
import os

version = '0.1.3.'

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
          'six>=1.10.0'
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
