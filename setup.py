from setuptools import setup


with open('requirements.txt') as fp:
    install_requires = fp.read()

setup(
    name='dendro_text',
    version='0.11.1',
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'dendro_text=dendro_text:main',
        ],
    },
)
