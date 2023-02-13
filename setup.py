"""
This is a generic setup file for creating a package.
It assumes that all the package details, like __version__, present in module's __init__.py
If it finds more than one module to pack then the first module's details would be present in the package metadata
In most cases, setup.cfg and MANIFEST.in are not required.

This is not the primary way of installing ordered-set.

The primary setup is in pyproject.toml.
You can install stableset as a dependency using `poetry` or `pip`.
"""

__author__ = "Idan Miara"

import glob
import importlib
import os
import re
from typing import Dict, Any
from warnings import warn

from setuptools import setup, find_packages


def get_requirements() -> Dict[str, Any]:
    """
    parsing the main requirement file `requirements.txt` and any extra requirements files, like `requirements-dev.txt
    and returns a requirements dict to use with setup
    """
    requirements = {
        re.match(r"requirements-(.*).txt", x).group(1): x
        for x in glob.glob("requirements-*.txt")
    }
    if os.path.isfile("requirements.txt"):
        requirements[""] = "requirements.txt"
    requirements = {
        # read requirements from files and skip extra-index-url and empty lines
        r: [
            req.strip()
            for req in open(filename).readlines()
            if req.strip() and not req.startswith("--")
        ]
        for r, filename in requirements.items()
    }
    requirements = {
        r: req for r, req in requirements.items() if req
    }  # remove empty requirements
    result = {}
    if requirements.get(""):
        result["install_requires"] = requirements.pop("")

    if requirements:
        result["extras_require"] = requirements
    return result


def get_setup_kwargs(m: object, attrs=None) -> dict:
    if attrs is None:
        attrs = [
            "name",
            "version",
            "author",
            "author_email",
            "maintainer",
            "maintainer_email",
            "license",
            "url",
            "description",
            "long_description",
            "classifiers",
            "python_requires",
        ]

    # result = {k: v for k in attrs if (v := getattr(m, f'__{k}__', None)) is not None}
    result = {k: getattr(m, f"__{k}__", None) for k in attrs}
    result = {k: v for k, v in result.items() if v is not None}

    # if python_minimum_version := getattr(m, '__python_minimum_version__', None):
    python_minimum_version = getattr(m, "__python_minimum_version__", None)
    if python_minimum_version is not None:
        result.setdefault("python_requires", f">={python_minimum_version}")

    for filename, fmt in ("README.md", "text/markdown"), ("README.rst", "text/x-rst"):
        if os.path.exists(filename):
            result["long_description"] = open(filename, encoding="utf-8").read()
            result["long_description_content_type"] = fmt
        break

    result.update(get_requirements())
    return result


package_root = "."  # package sources are under this dir
packages = find_packages(package_root)  # include all packages under package_root
package_dir = {"": package_root}  # packages sources are under package_root

module_names = sorted(set(p.split(".")[0] for p in packages))
if len(module_names) == 0:
    raise Exception(f"Could not find any module_names in {package_root}")
elif len(module_names) > 1:
    warn(
        f"There is more than 1 module in this package - {module_names}. "
        f"Assuming this is not a mistake - "
        f"All these modules would be packaged inside a single package "
        f"with the package name and metadata would taken from the first module: "
        f"{module_names[0]}"
    )

module = importlib.import_module(module_names[0])
kwargs = get_setup_kwargs(module)

setup(
    **kwargs,
    packages=packages,
    package_dir=package_dir,
    package_data={"": ["resources/*.json", "resources/*.csv", "resources/*.osm"]},
)
