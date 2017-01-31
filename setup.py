import setuptools

from setuptools import setup, find_packages
from codecs import open
from os import path

__version__ = '0.0.1'
here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='neutron-trace-profiler',

    version=__version__,
    description='Neutron low level function call trace profiler',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/venkataanil/neutron-trace-profiler',

    # Author details
    author='Venkata Anil, Daniel Alvarez',
    author_email='anilvenkata@redhat.com, dalvarez@redhat.com',

    # Choose your license
    license='Apache Software License',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: End Users/Desktop',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Utilities',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7',
    ],

    # What does your project relate to?
    keywords='neutron-trace-profiler',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    py_modules=['neutron_trace_profiler.profiler', 'neutron_trace_profiler.server'],
    install_requires=['GreenletProfiler'],

    entry_points={
        'neutron.agent.l2.extensions': [
            'trace_profiler = neutron_trace_profiler.profiler:ProfilerAgentExtension',],
        'neutron.agent.l3.extensions': [
            'trace_profiler = neutron_trace_profiler.profiler:ProfilerAgentExtension',]
    },
)
