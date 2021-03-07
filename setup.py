from setuptools import setup, find_packages


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Bot-a-Plot",
    version="0.1.0",
    author="Derek Anderson",
    author_email="enki+botaplot@armyofevilrobots.com",
    description="Plotter management and generative art environment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    zip_safe=False,
    url="https://armyofevilrobots.com",
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    include_package_data=True,
    scripts=["scripts/botaplot", "scripts/botaplot_svg2gcode", "scripts/botaplot-print"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPLv3 License",
        "Operating System :: OS Independent",
    ],
)

