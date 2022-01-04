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
import os.path as p
import sys
import yaml
import types
import inspect

sys.path.insert(0, p.abspath('../..'))

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


class Coverage:
    """
    handler for code coverage to replace shortcomings with sphinx's coverage

    Add to conf.py:

    def setup(app):
        Coverage(app)

    Args:
        app:
            sphinx-build app, for connections
    """

    DEBUG = True

    def __init__(self, app, logfile='coverage.yml'):

        # initialise connections with the sphinx builder
        self._connect_funcs(app)

        # logfile to output coverage stats to
        self._logpath = self._create_log(logfile)
        self._autodoc = False  # don't output if there's no autodoc

        # custom counted object list
        self.objects = []

        # section tracking
        self._current_section = ''
        # self._current__file__ = ''
        self._current_loader = ''
        self._sourcefile = ''

        # exclude patterns
        self.exclude_startswith = ['__',  # catch dunder functions
                                   'test_',  # ignore any tests
                                   '_',  # private members
                                   ]

    def _connect_funcs(self, app):
        app.connect('autodoc-skip-member', self.autodoc_skip)
        app.connect('source-read', self.source_read)
        app.connect('build-finished', self.finish)
        app.connect('autodoc-process-signature', self.obj_prepro)

    def _eliminate_by_name(self, name):
        """eliminate objects based on their name"""

        skip = any(name.startswith(pattern) for pattern in
                   self.exclude_startswith)

        return skip

    def autodoc_skip(self, app, what, name, obj, skip, options):
        """Determine whether to skip this object

        Returns:
            (bool) skip:
                skip flag passed back to autodoc. True to skip documentation
        """
        self._autodoc = True

        if self._eliminate_by_name(name):
            # no point checking for docstring if we're skipping anyway
            return True

        # need to know if we're at the start of the module
        mode_module = False
        if self._current_section == self._sourcefile:
            mode_module = True

        if self.DEBUG:
            print('\t', name, what, type(obj), end=' ')

        # manage undocumented sections
        empty_doc = True
        if hasattr(obj, '__doc__'):
            empty_doc = False
            docstr = obj.__doc__

            if docstr is None:
                empty_doc = True
            if docstr == '':
                empty_doc = True
            if docstr == 'skip':
                # skip documenting this object
                # as it still _has_ a docstring, should still be caught
                # TODO: verify
                empty_doc = True

        if empty_doc:
            if self.DEBUG:
                print(f'no doc for {name}')

        elif self.DEBUG:
            print()

        return empty_doc

    def _create_log(self, logname):
        import os
        logpath = os.path.abspath(logname)
        print('coverage log will be created at ' + logpath)

        return logpath

    def finish(self, app, exception):
        """Connect to sphinx event `build-finished(app, exception)`

        Final cleanup, calculation and output of coverage stats
        """

        if not self._autodoc:
            print('coverage not outputting: autodoc was never called'
                  '(use apidoc to create sourcefiles)')
            return None

        initial_log_line = 'Undocumented Objects:'

        print('Coverage analysis complete, writing log at ' +
              self._logpath)

        sphinx_objects = list(app.env.domaindata['py']['objects'].keys())
        undoc = sorted(list(set(self.objects) - set(sphinx_objects)))
        undoc_pc = 100 - 100 * len(undoc) / len(self.objects)

        if self.DEBUG:
            print('#' * 24 + ' Documented objects:')
            print(sphinx_objects)
            print('#' * 24 + ' Objects found in source:')
            print(self.objects)
            print('#' * 24 + ' Undocumented objects:')
            print(undoc)
            print('#'*24 + ' Results:')
        print(f'Code coverage percentage: {undoc_pc:.2f}')

        with open(self._logpath, 'w+') as o:
            yaml.dump({'Undocumented objects': undoc,
                       'Coverage Percentage': undoc_pc}, o)

    def source_read(self, app, docname, source):
        """Hook into sphinx source read function"""
        name = docname.split('/')[-1]
        self._sourcefile = name
        if self.DEBUG:
            print()
            print('new sourcefile', name)

    def _count_object(self, objname, obj, rootname, depth=0):
        """recursively count store for comparison

        Args:
            objname (str):
                name of the object
            obj (object):
                object itself (for recursion and other checks)
            rootname (str):
                call path up until now
            depth:
                tab indentation for debugging recursion
        returns:
            None
        """
        appname = rootname + '.' + objname
        if self.DEBUG:
            print('\t' * depth + f'considering {appname}', end='... ')
        msg = []

        skip = False

        # remove same names as autodoc
        if self._eliminate_by_name(objname):
            skip = True
            msg.append('blacklisted name, ')

        # avoids most imports
        # if hasattr(obj, '__file__'):
        #     if obj.__file__ != self._current__file__:
        #         skip = True
        #         msg.append('external import, ')

        if hasattr(obj, '__loader__'):
            if obj.__loader__ != self._current_loader:
                skip = True
                msg.append('loader mismatch (external import?), ')

        # skip uncallables (but NOT properties!)
        if not hasattr(obj, '__call__'):
            if not hasattr(obj, '__set__'):
                skip = True
                msg.append('non callable structure, ')

        if hasattr(obj, '__module__'):
            if obj.__module__ != self._current_section:
                skip = True
                msg.append('module mismatch (local import from '
                           f'{obj.__module__}), ')

            elif not skip:
                # also recursively grab members, if we're not already skipping
                for membername, member in vars(obj).items():
                    self._count_object(membername, member,
                                       appname, depth + 1)

        # specific debugging
        # if objname in ['TEST', 'endpoint']:
        #     print('\nspecified debugging for ', objname)
        #     print(dir(obj))

        if not skip:
            self.objects.append(appname)
            if self.DEBUG:
                print('appended as', appname)
        elif self.DEBUG:
            print(''.join(msg)[:-2] + '. Skipped.')

    def obj_prepro(self, app, what, name, obj, options, signature,
                   return_annotation):
        """Hook into sphinx object call and store the object members"""
        if self.DEBUG:
            print('new section,', name)
        self._current_section = name

        # self._current__file__ = getattr(obj, '__file__', '')
        self._current_loader = getattr(obj, '__loader__', '')

        modname = getattr(obj, '__module__', None)
        # loader = getattr(obj, '__loader__', None)

        # if this object is a module, get its members for comparison
        if isinstance(obj, types.ModuleType):
            if self.DEBUG:
                print('moduletype', name, modname)

            for membername, member in vars(obj).items():
                self._count_object(membername, member, name, depth=1)


def setup(app):
    coverage_handler = Coverage(app)
