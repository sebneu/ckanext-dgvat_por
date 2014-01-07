from setuptools import setup, find_packages
import sys, os


version = '1.2.1'


setup(
	name='ckanext-dgvat_por',
	version=version,
	description="data.gv.at Plugin for backend",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='BRZ GesmbH',
	author_email='data@brz.gv.at',
	url='www.brz.gv.at',
	license='GPL',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.dgvat_por', 'repoze', 'repoze.who', 'repoze.who.plugins'],
	include_package_data=True,
	package_data={'ckan': ['i18n/*/LC_MESSAGES/*.mo']},
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
	"""
        [ckan.plugins]
        datagvatpor = ckanext.dgvat_por.plugin:DgvatForm
        #datagvatpor_solr = ckanext.dgvat_por.plugin:DgvatForm
		
        [ckan.forms]
        #data_gv_at = ckanext.dgvat.forms.data_gv_at:get_dgvat_fieldset
	    
	# Add plugins here, eg
	# myplugin=ckanext.dgvat_por:PluginClass
	""",
)
