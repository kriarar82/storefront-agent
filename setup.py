"""Setup script for the Storefront Agent package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
requirements = []
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="storefront-agent",
    version="1.0.0",
    author="Storefront Agent Team",
    author_email="team@storefront-agent.com",
    description="AI-powered agent for storefront operations using Azure LLM and MCP servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/storefront-agent",
    project_urls={
        "Bug Reports": "https://github.com/your-org/storefront-agent/issues",
        "Source": "https://github.com/your-org/storefront-agent",
        "Documentation": "https://github.com/your-org/storefront-agent/blob/main/README.md",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
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
        "Topic :: Office/Business",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "storefront-agent=storefront_agent.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "storefront_agent": ["*.yaml", "*.yml", "*.json"],
    },
    keywords="ai agent llm azure mcp storefront ecommerce",
    zip_safe=False,
)