"""Setup configuration for agent-bot package."""

from setuptools import setup, find_packages

setup(
    name="agent-bot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot>=20.0",
        "sqlalchemy>=2.0",
        "pyyaml>=6.0",
        "arabic-reshaper>=3.0",
        "numpy>=1.24",
    ],
    python_requires=">=3.8",
)
