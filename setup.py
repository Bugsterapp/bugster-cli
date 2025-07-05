import re

from setuptools import find_packages, setup

# Read version from bugster/__init__.py
with open("bugster/__init__.py", encoding="utf-8") as f:
    version_match = re.search(r'__version__ = ["\']([^"\']*)["\']', f.read())
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")

setup(
    name="bugster",
    version=version,
    packages=find_packages(),
    install_requires=[
        "aiohappyeyeballs==2.6.1",
        "aiohttp==3.11.18",
        "aiosignal==1.3.2",
        "altgraph==0.17.4",
        "annotated-types==0.7.0",
        "anyio==4.9.0",
        "attrs==25.3.0",
        "certifi==2025.6.15",
        "charset-normalizer==3.4.2",
        "click==8.2.1",
        "gitdb==4.0.12",
        "GitPython==3.1.44",
        "loguru==0.7.3",
        "macholib==1.16.3",
        "h11==0.16.0",
        "httpcore==1.0.9",
        "httpx==0.28.1",
        "httpx-sse==0.4.1",
        "huggingface-hub==0.31.4",
        "idna==3.10",
        "markdown-it-py==3.0.0",
        "MarkupSafe==3.0.2",
        "mcp==1.10.0",
        "mdurl==0.1.2",
        "packaging==25.0",
        "pathspec==0.12.1",
        "posthog==5.0.0",
        "pydantic==2.11.7",
        "pydantic-settings==2.9.1",
        "pydantic_core==2.35.2",
        "Pygments==2.19.1",
        "pyinstaller-hooks-contrib==2025.5",
        "python-dotenv==1.1.0",
        "python-multipart==0.0.20",
        "PyYAML==6.0.2",
        "referencing==0.36.2",
        "regex==2024.11.6",
        "requests==2.32.4",
        "rich==14.0.0",
        "rpds-py==0.25.1",
        "shellingham==1.5.4",
        "smmap==5.0.2",
        "sniffio==1.3.1",
        "sse-starlette==2.3.5",
        "starlette==0.47.1",
        "typer==0.15.4",
        "types-requests==2.32.4.20250611",
        "typing-inspection==0.4.1",
        "typing_extensions==4.13.2",
        "urllib3==2.5.0",
        "uvicorn==0.34.2",
        "websockets==15.0.1",
        "yarl==1.20.0",
        "zipp==3.21.0",
    
    ],
    entry_points={
        "console_scripts": [
            "bugster=bugster.cli:main",
        ],
    },
    author="Bugster Team",
    description="A CLI tool for managing test cases",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    keywords="testing, cli, automation",
    python_requires=">=3.10",
)
