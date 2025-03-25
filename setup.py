from setuptools import setup, find_packages

setup(
    name="contact-cleaner",
    version="0.1.0",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'pandas>=1.3.0',
    ],
    entry_points={
        'console_scripts': [
            'contact-cleaner=cli:main',
        ],
    },
    python_requires='>=3.8',
)
