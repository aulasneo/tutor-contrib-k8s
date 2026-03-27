"""
Setuptools for Tutor-contrib-k8s
"""
import io
import os

from setuptools import find_packages, setup

HERE = os.path.abspath(os.path.dirname(__file__))


def load_readme():
    """
    Load readme file.
    :return:
    """
    with io.open(os.path.join(HERE, "README.rst"), "rt", encoding="utf8") as f:
        return f.read()


def load_about():
    """
    Load about file.
    :return:
    """
    about = {}
    with io.open(
        os.path.join(HERE, "tutork8s", "__about__.py"),
        "rt",
        encoding="utf-8",
    ) as f:
        exec(f.read(), about)  # pylint: disable=exec-used
    return about


ABOUT = load_about()


setup(
    name="tutor-contrib-k8s",
    version=ABOUT["__version__"],
    url="https://github.com/aulasneo/tutor-contrib-k8s",
    project_urls={
        "Code": "https://github.com/aulasneo/tutor-contrib-k8s",
        "Issue tracker": "https://github.com/aulasneo/tutor-contrib-k8s/issues",
    },
    license="AGPLv3",
    author="Aulasneo",
    author_email="andres@aulasneo.com",
    description="Helper plugin for Kubernetes deployments of Open edX",
    long_description=load_readme(),
    long_description_content_type="text/x-rst",
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=["tutor >= 20.0.0, < 21.0.0"],
    entry_points={"tutor.plugin.v1": ["k8s = tutork8s.plugin"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
