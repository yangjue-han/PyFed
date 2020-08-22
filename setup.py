import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyfed",
    version="0.0.1",
    author="Felix Han",
    author_email="yangjue.han20@gmail.com",
    description="A Python package for processing the Federal Reserve's data.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yangjue-han/PyFed",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='==3.6',
    install_requires=[
        'fredapi',
        'quandl',
        'numpy',
        'pandas',
        'scipy',
        'seaborn',
        'matplotlib']
)
