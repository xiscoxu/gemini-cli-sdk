"""Setup script for Gemini CLI SDK."""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Only include core dependencies, not dev dependencies
                    if not any(dev_dep in line for dev_dep in ['pytest', 'black', 'flake8', 'mypy', 'sphinx']):
                        requirements.append(line)
    return requirements

setup(
    name="gemini-cli-sdk",
    version="1.0.5",
    author="xiscoxu",
    author_email="xuxisco@gmail.com",
    description="A Python SDK for interacting with Gemini CLI",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/xiscoxu/gemini-cli-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Communications :: Chat",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "aioresponses>=0.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gemini-cli-sdk=gemini_cli_sdk.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "gemini",
        "cli",
        "sdk",
        "ai",
        "chatbot",
        "conversation",
        "async",
        "python",
    ],
    project_urls={
        "Bug Reports": "https://github.com/xiscoxu/gemini-cli-sdk/issues",
        "Source": "https://github.com/xiscoxu/gemini-cli-sdk",
        "Documentation": "https://gemini-cli-sdk.readthedocs.io/",
    },
)
