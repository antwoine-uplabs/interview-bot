from setuptools import setup, find_packages

setup(
    name="interview-evaluator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.95.0",
        "pydantic>=2.0.0",
        "sentry-sdk>=1.24.0",
        "httpx>=0.24.0",
    ],
)