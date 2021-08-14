from pathlib import Path

from setuptools import setup  # type: ignore

DIR = Path(__file__).parent

setup(
    name="filament",
    version="0.0.2",
    description="Serialization of python objects to/from JSON.",
    long_description=(DIR / "README.md").read_text(),
    long_description_content_type="text/markdown",
    url="https://github.com/marticongost/filament",
    author="Martí Congost",
    author_email="marticongost@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    packages=["filament"],
    include_package_data=True,
    install_requires=["pytest==6.2.*"],
    python_requires=">=3.9.*",
)
