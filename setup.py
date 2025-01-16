from setuptools import setup, find_packages

setup(
    name="dxrpy",
    version="0.2.7",
    description="A client library for DXR",
    author="Darko Stanimirovic",
    author_email="dstanimirovic@ohalo.co",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[],
)
