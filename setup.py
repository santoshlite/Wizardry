from setuptools import setup

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setup(
    name='wizardry',
    version='0.1',
    description='Wizardry is a CLI for building and picking algorithmic trading strategy (for QC)',
    py_modules=['wizardry'],
    package_dir={'':'src'},
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url='https://github.com/ssantoshp/Wizardryr',
    author = "Santosh Passoubady",
    author_email = "santoshpassoubady@gmail.com",
    license='MIT',
    install_requires=[
          'pyfiglet',
          'PyInquirer',
          'typer'
      ],
)
