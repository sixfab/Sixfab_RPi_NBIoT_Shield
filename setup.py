from setuptools import setup, find_packages

setup(
    name='sixfab_nbiot',
    version='1.0.0',
    author='Yasin Kaya',
    author_email='yasinkaya.121@gmail.com',
    description='sixfab nbiot library for rpi',
    license='MIT',
    url='https://github.com/sixfab/Sixfab_RPi_NBIoT_Library',
    dependency_links  = ['https://github.com/adafruit/Adafruit_Python_GPIO/tarball/master#egg=Adafruit-GPIO-0.9.3'],
	install_requires  = ['Adafruit-GPIO>=0.9.3', 'pyserial', 'adafruit-ads1x15'],
    packages=find_packages()
)
