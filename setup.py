from setuptools import setup, find_packages

setup(
    name="appimagecraft",
    version="0.0.1",
    packages=find_packages(),
    license="MIT",
    long_description=open("README.md").read(),
    install_requires=[
        "PyYAML",
        "coloredlogs",
    ],
    entry_points={
        "console_scripts": [
            "appimagecraft = appimagecraft._cli:run",
        ],
    },
)
