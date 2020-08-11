from setuptools import setup

setup(
    name='solarannotator',
    version='0.1',
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
                      "goes-solar-retriever"],
    data_files=[('solarannotator', ['cfg/default.json'])],
    entry_points={"console_scripts": ["SolarAnnotator = solarannotator.main:main"]}

)
