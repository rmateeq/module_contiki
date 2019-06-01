from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='wishful_module_gitar',
    version='1.1.0',
    packages=[
        'communication_wrappers', 
        'communication_wrappers.bin', 
        'wishful_module_gitar', 
        'wishful_module_generic', 
        'wishful_module_contikibase', 
        'wishful_module_taisc', 
        'wishful_module_rime', 
        'wishful_module_ipv6', 
        'wishful_module_lpl_csma', 
        'wishful_module_nullrdc_csma'
    ],
    package_data={
        'communication_wrappers.bin': ['*']
    },
    url='http://www.wishful-project.eu/software',
    license='',
    author='Peter Ruckebusch',
    author_email='peter.ruckebusch@intec.ugent.be',
    description='WiSHFUL Contiki Module',
    long_description='Implementation of a Contiki agent using the unified programming interfaces (UPIs) of the Wishful project.',
    keywords='wireless control',
    install_requires=['configparser', "enum34", "crc16", "pyserial", "construct"]  # ,"coapthon"]
)
