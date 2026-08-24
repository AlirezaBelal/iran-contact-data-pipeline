from setuptools import setup

setup(
    name="iran-contact-data-pipeline",
    version="0.2.0",
    description="CLI pipeline for normalizing Iranian contact data and selecting valid mobile numbers.",
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
)
