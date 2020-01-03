import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='Estrade',
    version='0.0.1',
    author='Gabriel Oger',
    author_email='gabriel.oger@gmail.com',
    description='Build, Backtest and Go Live your own trading bots',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/cimourdain/estrade',
    packages=setuptools.find_packages(),
    classifiers=[
        'Development Status :: 1 - Planning',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6,<3.7',
    install_requires=[
        "arrow",
        "marshmallow>=3",
        "python-dateutil",
        "pytz",
        "pyYAML",
        "requests",
        "setuptools",
    ]
)
