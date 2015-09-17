from setuptools import setup, find_packages

version = {}
with open("common/version.py") as fp:
    exec(fp.read(), version)
version = version['__version__']

long_description = open('README.rst').read()

setup(
    name='zoe-analytics',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version,

    description='Zoe - Analytics on demand',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/DistributedSystemsGroup/zoe',

    # Author details
    author='Daniele Venzano',
    author_email='venza@brownhat.org',

    # Choose your license
    license='Apache 2.0',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        'Environment :: Web Environment',
        'Framework :: IPython',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Education',
        'Operating System :: POSIX :: Linux',
        'Topic :: Software Development',
        'Topic :: System :: Distributed Computing',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: Apache Software License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
    ],

    # What does your project relate to?
    keywords='spark analytics docker swarm containers notebook',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['scripts', 'tests']),

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['docker-py>=1.3.0',
                      'Flask>=0.10.1',
                      'python-dateutil>=2.4.2',
                      'SQLAlchemy>=1.0.8',
                      'tornado>=4.2.1',
                      'pyzmq>=14.0.1'
                      ],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': ['Sphinx'],
        'test': ['coverage', 'pytest'],
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        '': ['*.sh', '*.conf', '*.rst', '*.css', '*.js', '*.html'],
    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'zoe-manage=zoe_scheduler.entrypoint:zoe_manage',
            'zoe-scheduler=zoe_scheduler.entrypoint:zoe_scheduler',
            'zoe-web=zoe_web.entrypoint:zoe_web',
            'zoe=zoe_client.entrypoint:zoe'
        ]
    }
)
