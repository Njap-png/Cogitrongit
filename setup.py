"""PHANTOM setup.py - Package installation."""

from setuptools import setup, find_packages
from pathlib import Path

here = Path(__file__).parent
long_description = ""

try:
    readme = here / "README.md"
    if readme.exists():
        long_description = readme.read_text(encoding="utf-8")
except Exception:
    pass

setup(
    name="phantom-ai",
    version="2.0.0",
    description="Polymorphic Heuristic AI for Network Threat Analysis & Mentoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="PHANTOM-CORE PROJECT",
    author_email="phantom@phantom-ai.dev",
    url="https://github.com/Njap-png/Cogitrongit",
    project_urls={
        "Bug Tracker": "https://github.com/Njap-png/Cogitrongit/issues",
        "Source": "https://github.com/Njap-png/Cogitrongit",
    },
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={
        "phantom": ["data/**/*.json", "data/**/*.yaml"],
    },
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "httpx>=0.24.0",
        "beautifulsoup4>=4.11.0",
        "lxml>=4.9.0",
        "rich>=13.0.0",
        "prompt_toolkit>=3.0.0",
        "duckduckgo-search>=3.0.0",
        "markdownify>=0.11.0",
        "html2text>=2020.1.16",
        "readability-lxml>=0.8.1",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0",
        "click>=8.1.0",
        "aiohttp>=3.8.0",
        "anthropic>=0.20.0",
        "openai>=1.0.0",
        "google-generativeai>=0.3.0",
        "colorama>=0.4.6",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
        "minimal": [
            "requests>=2.28.0",
            "beautifulsoup4>=4.11.0",
            "rich>=13.0.0",
            "duckduckgo-search>=3.0.0",
            "html2text>=2020.1.16",
            "python-dotenv>=1.0.0",
            "pyyaml>=6.0",
            "colorama>=0.4.6",
        ],
    },
    entry_points={
        "console_scripts": [
            "phantom=phantom.phantom:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: Education",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords=[
        "cybersecurity",
        "ai",
        "threat-analysis",
        "penetration-testing",
        "ctf",
        "education",
        "security-research",
    ],
    zip_safe=False,
)