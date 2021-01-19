from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Bot-a-Plot", # Replace with your own username
    version="0.0.1",
    author="Derek Anderson",
    author_email="enki+botaplot@armyofevilrobots.com",
    description="Plotter management and generative art environment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://armyofevilrobots.com",
    package_dir={'': 'src'},
    scripts=["scripts/botaplot", ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPLv3 License",
        "Operating System :: OS Independent",
    ],
)

