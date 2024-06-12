from setuptools import setup, find_packages

setup(
    name="pyfuncschedule",
    version="0.1",
    author="Benedict Wilkins",
    author_email="benrjw@gmail.com",
    description="",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pyparsing"],
    python_requires=">=3.10",
)
