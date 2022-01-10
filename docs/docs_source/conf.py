# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import os.path as p
import sys

package_root = p.abspath('../..')
print(package_root)

sys.path.insert(0, package_root)
sys.path.insert(0, package_root+'/Coverage')

from Coverage import CoverageHandler

DEBUG = True

# -- Project information -----------------------------------------------------

project = 'VoronoiTest'
copyright = '2021, LBeal'
author = 'LBeal'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx_rtd_theme',
              'sphinx.ext.napoleon',
              'sphinx.ext.autodoc',
              ]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# don't test coverage for unittest tests
coverage_ignore_pyobjects = ['test_*']

autodoc_member_order = 'bysource'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['../_static']


# sphinx-apidoc -f -o ./docs/docs_source/apidoc/ -t ./docs/_templates/ .
# sphinx-build -E -a -b html ./docs/docs_source/ ./docs/
# sphinx-build -E -a -b coverage ./docs/docs_source/ ./docs/


def setup(app):
    coverage_handler = CoverageHandler(app)
