from setuptools import setup, find_packages

def readme():
	with open('README.md') as f:
		return f.read()

setup(
	name='wishful_module_gitar',
	version='1.1.0',
	packages=find_packages(),
	url='http://www.wishful-project.eu/software',
	license='',
	author='Peter Ruckebusch',
	author_email='peter.ruckebusch@intec.ugent.be',
	description='WiSHFUL Contiki Module',
	long_description='Implementation of a Contiki agent using the unified programming interfaces (UPIs) of the Wishful project.',
	keywords='wireless control',
	install_requires=['ConfigParser',"enum34"]
)
