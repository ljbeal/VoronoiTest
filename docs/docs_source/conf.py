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
import inspect
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))


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


class Coverage:
    """
    handler for code coverage to replace shortcomings with sphinx's coverage


    Add to conf.py:


    def setup(app):
        coverage_handler = Coverage()
        app.connect('autodoc-skip-member', coverage_handler.autodoc_skip)
        app.connect('source-read', coverage_handler.source_read)
        app.connect('build-finished', coverage_handler.finish)

    """

    def __init__(self, logfile='coverage.txt'):

        self._logpath = self._create_log(logfile)
        self._sections = {}

        self._count = 0  # counter for total modules considered

        self._current_doc = ''

        self._tree = {}

    def autodoc_skip(self, app, what, name, obj, skip, options):

        # start patterns to exclude from autodoc
        exclude_startswith = ['__',  # catch dunder functions
                              'test_',  # ignore any tests
                              ]

        skip_start = any(name.startswith(pattern)
                         for pattern in exclude_startswith)

        if skip_start:
            # no point checking for docstring if we're skipping anyway
            return True

        self._count += 1

        # manage undocumented sections
        empty_doc = True
        if hasattr(obj, '__doc__'):
            empty_doc = False
            docstr = obj.__doc__

            if docstr is None:
                empty_doc = True
            if docstr == '':
                empty_doc = True

        print(name)
        if empty_doc and not skip_start:
            self._update_log(name)

        return empty_doc

    def _update_tree(self, pydomain):

        for obj in pydomain['objects']:
            leafpath = obj.split('.')
            print(leafpath)

            # self._tree[leafpath[0]] = self._make_branch(leafpath)


    def _make_branch(self, leafpath):
        print('adding', leafpath[0])
        stub = {}

        stub[leafpath[0]] = self._make_branch([leafpath[1:]])

        return stub

    def source_read(self, app, docname, source):
        # reading a new source file, create a section

        print('#'*24)
        for item in app.env.domains['py'].get_objects():
            print(item)

        end = os.path.split(docname)[-1]

        self._current_doc = end

        end = os.path.split(docname)[-1]

        self._sections[end] = []

    def _create_log(self, logname):
        import os
        logpath = os.path.abspath(logname)
        print('coverage log will be created at ' + logpath)

        return logpath

    def _update_log(self, name):

        self._sections[self._current_doc].append(name)

    def finish(self, app, exception):
        """Connect to sphinx event `build-finished(app, exception)`"""

        initial_log_line = 'Undocumented Objects:'

        print('Coverage analysis complete, writing log at ' +
              self._logpath)

        undoc_count = 0

        with open(self._logpath, 'w+') as o:
            o.write(initial_log_line+'\n')
            o.write('='*len(initial_log_line) + '\n\n')

            for doc, section in self._sections.items():
                if len(section) > 0:
                    o.write(doc + '\n')
                    o.write('-'*len(doc) + '\n')
                    for line in section:
                        o.write(f'- {line}\n')
                        undoc_count += 1
                    o.write('\n')

            undoc_pc = 100 - (100 * undoc_count / self._count)
            o.write('\nCoverage')
            o.write('\n'+'-'*8)
            o.write(f'\n{undoc_count} undocumented of {self._count} objects')
            o.write(f'\n==> {undoc_pc:.2f}% coverage')


def setup(app):
    coverage_handler = Coverage()
    app.connect('autodoc-skip-member', coverage_handler.autodoc_skip)
    app.connect('source-read', coverage_handler.source_read)
    app.connect('build-finished', coverage_handler.finish)
