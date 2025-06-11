from setuptools import setup, find_packages

setup(
    name="obento_test",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn[standard]",
        "asyncpg"
    ]
)
