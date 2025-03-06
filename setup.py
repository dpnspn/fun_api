from setuptools import setup, find_packages

setup(
    name='fun_api',
    version='0.0.1',
    description='FunCode Student API',
    author='moontr3',
    packages=find_packages(),
    install_requires=['requests'],
    zip_safe=False
)