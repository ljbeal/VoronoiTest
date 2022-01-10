import types
import yaml


class DocObject:
    """Object for storing documentation information

    initialised from the call name (fullname), but provides functionality for
    assessing the docstring of the object
    """

    # eliminate objects whose name begins with these
    exclude_startswith = ['__',
                          '_',
                          'test_',
                          ]

    skip_startswith = ['#skip',
                       '!skip']

    def __init__(self, fullname):

        self._set_names(fullname)

        self._docstring = ""
        self._skip = True
        self._skip_flag = False
        self._skip_reason = 'state not modified from init'
        # object must be validated by recursive inspection
        self._validated = False
        self._subclasses = []

    def __repr__(self):

        ret = f'documentation object representing {self._fullname}' \
              f' (has {len(self._subclasses)} subclasses)'

        return ret

    def _set_names(self, fullname):

        self._fullname = fullname
        self._call_structure = fullname.split('.')
        self._name = self._call_structure[-1]

    def _eliminate_by_name(self):
        """eliminate objects based on their name"""

        skip = any(self._name.startswith(pattern) for pattern in
                   self.exclude_startswith)

        return skip

    def validate(self):
        """validate this object as a geniune non-inherited object"""
        self._validated = True

    @property
    def name(self):
        """final portion of call name (method/func/class name)"""
        return self._name

    @property
    def fullname(self):
        """full callable name of the object

        e.g. module.class.method
        """
        return self._fullname

    @property
    def call_structure(self):
        return self._call_structure

    @property
    def docstring(self):
        """object docstring"""
        return self._docstring

    @docstring.setter
    def docstring(self, doc):
        """parse and set the docstring for the object"""

        if doc is None:
            doc = ""

        # make sure the docstring is clean, for checking
        doc = doc.strip()

        if any([doc.startswith(pattern) for
                pattern in self.skip_startswith]):
            self._skip_flag = True

        self._docstring = doc

    @property
    def hasdoc(self):
        """return true if the docstring is populated

        DOES NOT CONSIDER SKIP FLAGS
        """
        return self._docstring != ""

    def _query_skip(self):
        """determine if this object should be skipped in the documentation"""
        if not self._validated:
            self._skip_reason = 'object not validated by prepro'
            return True

        if self._eliminate_by_name():
            self._skip_reason = 'blacklisted name'
            return True

        if self._skip_flag:
            self._skip_reason = 'skip flag'
            return True

        self._skip_reason = ''
        return False

    @property
    def skip(self):
        return self._query_skip()

    @property
    def skip_flag(self):
        """object has been force skipped via a skip docstring"""
        return self._skip_flag

    def add_subclass(self, subclass):
        self._subclasses.append(subclass)

    @property
    def subclasses(self):
        return self._subclasses


class CoverageHandler:
    """
    handler for code coverage to replace shortcomings with sphinx's coverage

    Add to conf.py:

    def setup(app):
        Coverage(app)

    Args:
        app:
            sphinx-build app, for connections
    """

    DEBUG = False

    def __init__(self, app, logfile='coverage.yaml'):

        # initialise connections with the sphinx builder
        self._connect_funcs(app)

        # logfile to output coverage stats to
        self._logpath = self._create_log(logfile)
        self._autodoc = False  # don't output if there's no autodoc

        # custom counted object list
        self.objects = {}

        # section tracking
        self._current_section = ''
        self._current_loader = ''
        self._sourcefile = ''
        self._subclass_queue = {}

        # exclude patterns
        self.exclude_startswith = ['__',  # catch dunder functions
                                   'test_',  # ignore any tests
                                   '_',  # private members
                                   ]

    def _connect_funcs(self, app):
        app.connect('source-read', self.source_read)
        app.connect('autodoc-skip-member', self.autodoc_skip)
        app.connect('autodoc-process-signature', self.obj_prepro)
        app.connect('build-finished', self.finish)

    def _eliminate_by_name(self, name):
        """eliminate objects based on their name"""

        skip = any(name.startswith(pattern) for pattern in
                   self.exclude_startswith)

        return skip

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

        # need special handling for static and classmethods,
        # sphinx seems to grab the actual decorator rather than the function
        if hasattr(obj, '__func__'):
            obj = obj.__func__

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

        docobj = self._object_hook(appname, callsource='count_obj')
        if hasattr(obj, '__doc__'):
            docobj.docstring = obj.__doc__
        if not skip:
            docobj.validate()

        if hasattr(obj, '__subclasses__'):
            subclasses = [x.__name__ for x in obj.__subclasses__()]
            if len(subclasses) > 0:
                self._subclass_queue[obj] = {'subs':subclasses,
                                             'sourcename': appname}

        if objname in self._expanded_subclass_list:
            for o, l in self._subclass_queue.items():
                if objname in l['subs'] and issubclass(obj, o):
                    # print(objname, 'is a subclass of', l['sourcename'])
                    self._subclass_queue[o]['subs'].remove(objname)
                    self.objects[l['sourcename']].add_subclass(docobj)

        if not skip:
            if self.DEBUG:
                print('appended as', appname)
        elif self.DEBUG:
            print(''.join(msg)[:-2] + '. Skipped.')

    @property
    def _expanded_subclass_list(self):
        ret = []
        for l in self._subclass_queue.values():
            ret += l['subs']

        return ret

    def autodoc_skip(self, app, what, name, obj, skip, options):
        """Determine whether to skip this object

        Returns:
            (bool) skip:
                skip flag passed back to autodoc. True to skip documentation
        """
        self._autodoc = True
        appname = f'{self._current_section}.{name}'
        docobj = self._object_hook(appname, callsource='autodoc_skip')
        return not docobj.hasdoc

    def _object_hook(self, fullname, callsource = None):
        """return a DocObject instance for a documentation member

        Creates the entry if it does not already exist

        Args:
            fullname (str):
                full call path to the object

        Returns:
            DocObject:
                object instance for storing data
        """
        # print(callsource + ' called assessment passed for ' + fullname)

        if fullname not in self.objects:
            self.objects[fullname] = DocObject(fullname)

        return self.objects[fullname]

    def _create_log(self, logname):
        import os
        logpath = os.path.abspath(logname)
        print('coverage log will be created at ' + logpath)

        return logpath

    def source_read(self, app, docname, source):
        """Hook into sphinx source read function"""
        name = docname.split('/')[-1]
        self._sourcefile = name
        if self.DEBUG:
            print()
            print('new sourcefile', name)

    def finish(self, app, exception):
        """Connect to sphinx event `build-finished(app, exception)`

        Final cleanup, calculation and output of coverage stats
        """

        if not self._autodoc:
            print('coverage not outputting: autodoc was never called'
                  '(use apidoc to create sourcefiles)')
            return None

        undoc_objects = []
        skipped_objects = []
        n_obj = 0
        n_und = 0
        for name, obj in self.objects.items():
            # print(name, obj.skip, obj.hasdoc, obj._skip_reason)
            # if len(obj.subclasses) > 0:
            #     print(obj)
            if not obj.skip:
                n_obj += 1
                if not obj.hasdoc:
                    n_und += 1
                    undoc_objects.append(obj.fullname)

            elif obj.skip_flag:
                skipped_objects.append(obj.fullname)

        undoc_pc = 100 - (100 * n_und / n_obj)

        coverage_breakdown = f'{len(self.objects)}/{len(skipped_objects)}/{len(undoc_objects)}'

        print(f'Code coverage percentage: {undoc_pc:.2f}')
        print('undocumented objects:')
        print(sorted(undoc_objects))
        print('coverage breakdown (total/skip/undoc):', coverage_breakdown)
        print(f'writing to logfile at {self._logpath}')

        with open(self._logpath, 'w+') as o:
            yaml.dump({'Objects Undocumented': sorted(undoc_objects),
                       'Objects Skipped': sorted(skipped_objects),
                       'Coverage Percentage': undoc_pc,
                       'Coverage Breakdown (total/skip/undoc)': coverage_breakdown}, o)
