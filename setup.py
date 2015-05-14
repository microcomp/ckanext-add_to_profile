from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
    name='ckanext-add_to_profile',
    version=version,
    description="add link to profile",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Janos Farkas',
    author_email='farkas48@uniba.sk',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.add_to_profile'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
        [ckan.plugins]
        addplugin=ckanext.add_to_profile.plugin:AddLinkToProfilePlugin
        [babel.extractors]
        ckan = ckan.lib.extract:extract_ckan
    ''',
)
