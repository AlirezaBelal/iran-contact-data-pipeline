from pathlib import Path

from setuptools import setup

README = Path(__file__).with_name("README.md").read_text(encoding="utf-8")

setup(
    name="iran-contact-data-pipeline",
    version="0.2.0",
    description=(
        "CLI pipeline for normalizing Iranian contact data and selecting "
        "a preferred mobile number."
    ),
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/AlirezaBelal/iran-contact-data-pipeline",
    project_urls={
        "Portfolio": "https://alirezabelal.github.io/",
        "Source": "https://github.com/AlirezaBelal/iran-contact-data-pipeline",
    },
    package_dir={"": "src"},
    py_modules=[
        "cli",
        "constants",
        "contact_processor",
        "exceptions",
        "utils",
    ],
    install_requires=["pandas>=1.5,<3.0"],
    entry_points={
        "console_scripts": [
            "contact-cleaner=cli:main",
        ],
    },
    python_requires=">=3.9",
    keywords=[
        "contact-normalization",
        "data-cleaning",
        "data-pipeline",
        "etl",
        "iran",
        "phone-normalization",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
    ],
)
