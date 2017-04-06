#!/usr/bin/env python2.7

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from os import path
import os
import sys


class PyTest(TestCommand):
    """Run py.test with RAFCON tests

    Copied http://doc.pytest.org/en/latest/goodpractices.html#integrating-with-setuptools-python-setup-py-test-pytest-runner
    """
    # This allows the user to add custom parameters to py.test, e.g.
    # $ python setup.py test -a "-v"
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = '-vxs -p no:pytest_capturelog'

    def run_tests(self):
        import shlex
        import pytest  # import here, cause outside the eggs aren't loaded
        test_path = path.join(path.dirname(path.abspath(__file__)), 'tests')
        rafcon_path = path.join(path.dirname(path.abspath(__file__)), 'source')
        sys.path.insert(0, test_path)
        sys.path.insert(0, rafcon_path)
        os.environ["PYTHONPATH"] = rafcon_path + os.pathsep + test_path + os.pathsep + os.environ["PYTHONPATH"]
        error_number = pytest.main(shlex.split(self.pytest_args) + [path.join('tests', 'network_test')])
        if not error_number:
            error_number = pytest.main(shlex.split(self.pytest_args) + [path.join('tests', 'common')])
        sys.exit(error_number)


global_requirements = ['astroid', 'pylint', 'pyyaml', 'psutil', 'jsonconversion>=0.2', 'yaml_configuration',
                       'python-gtkmvc==1.99.1', 'gaphas>=0.7']

tarball_url = "https://rmc-intra02.robotic.dlr.de/~stei_fn/tarballs/"

setup(
    name='RAFCON',
    version='0.9.1',
    url='https://github.com/DLR-RM/RAFCON',
    license='EPL',
    author='Sebastian Brunner, Rico Belder, Franz Steinmetz',
    author_email='sebastian.brunner@dlr.de, rico.belder@dlr.de, franz.steinmetz@dlr.de',
    description='Develop your robotic tasks with hierarchical state machines using an intuitive graphical user '
                'interface',

    packages=find_packages('source'),
    package_dir={'': 'source'},  # tell distutils packages are under src

    package_data={
        # Include all config files
        '': ['*.yaml'],
        # Include all glade files
        'mvc': ['glade/*.glade'],
    },

    setup_requires=['Sphinx>=1.4', 'Pygments>=2.0'] + global_requirements,
    tests_require=['pytest', 'pytest-catchlog'] + global_requirements,
    install_requires=global_requirements,

    dependency_links=[
        tarball_url + "common-python_yaml_configuration-0.0.5-5-gb8feb9f.tar.gz#egg=yaml_configuration-0.0.5",
        tarball_url + "common-gtkmvc_dlr-e6663d8.tar.gz#egg=python-gtkmvc-1.99.1"
    ],

    cmdclass={'test': PyTest},

    keywords=('state machine', 'robotic', 'FSM', 'development', 'GUI', 'visual programming'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: X11 Applications',
        'Framework :: Robot Framework',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Manufacturing',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development',
        'Topic :: Utilities'
    ],

    zip_safe=False
)
