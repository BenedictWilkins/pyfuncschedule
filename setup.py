from setuptools import setup, find_packages

setup(
    name="pyfuncschedule",
    version="0.1",
    author="Benedict Wilkins",
    author_email="benrjw@gmail.com",
    description="A simple schedule parser/runner with a convienient syntax.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    url="https://github.com/BenedictWilkins/pyfuncschedule"
    install_requires=["pyparsing", "aiostream"],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.10",
    ],
)
