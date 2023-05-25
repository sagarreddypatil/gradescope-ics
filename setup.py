import setuptools

with open("README.md", "r", encoding = "utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "gscdash",
    version = "0.0.1",
    author = "Zack Ives",
    author_email = "zives@cis.upenn.edu",
    description = "Gradescope-Canvas Dashboard support",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/upenn/gradescope-canvas-dashboard",
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Gnu Afero Public License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "requests",
        "html5lib",
        "beautifulsoup4",
        "canvasapi",
        "pandas",
        "pytz",
        "pyyaml",
    ],
    package_dir = {"": "gscdash"},
    packages = setuptools.find_packages(where="gscdash"),
    python_requires = ">=3.9"
)