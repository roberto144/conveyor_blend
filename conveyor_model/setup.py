# setup.py
from setuptools import setup, find_packages

setup(
    name="conveyor-blending-model",
    version="1.0.0",
    description="A modular application for simulating material flow and blending on conveyor belts",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/conveyor-blending-model",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Engineering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyQt5>=5.15.0",
        "matplotlib>=3.3.0",
        "numpy>=1.20.0",
        "pandas>=1.3.0",  # Optional, for CSV export
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-qt>=4.0",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.910",
        ],
    },
    entry_points={
        "console_scripts": [
            "conveyor-model=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.json"],
    },
)

# requirements.txt