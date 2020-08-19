from setuptools import setup

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='solarannotator',
    long_description=long_description,
    long_description_content_type='text/markdown',
    version='0.2.9',
    packages=['solarannotator'],
    url='',
    license='',
    author='J. Marcus Hughes',
    author_email='j-marcus.hughes@noaa.gov',
    description='A tool to annotate images of the Sun',
    install_requires=["PyQt5",
                      "matplotlib",
                      "astropy",
                      "numpy",
                      "goes-solar-retriever",
                      "scipy",
                      "scikit-image",
                      "pillow"],
    data_files=[('solarannotator', ['cfg/default.json'])],
    entry_points={"console_scripts": ["SolarAnnotator = solarannotator.main:main"]}

)
