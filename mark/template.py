import os
import shlex
import subprocess

import jinja2
from jinja2 import meta

from mark.errors import MarkfileError, TemplateVariableError

def popen(command):
    try:
        return subprocess.check_output(shlex.split(command))
    except Exception as e:
        print "Warning, template subprocess failed:", e


class MarkfileLoader(jinja2.BaseLoader):

    def findFilename(self, filename, path=os.getcwd()):
        """
        Recursively search parent directories for the named file.
        """
        files = os.listdir(path)
        parent = os.path.dirname(path)
        if filename in files:
            fullpath = os.path.join(path, filename)
            return os.path.abspath(fullpath)
        elif parent != path:
            return self.findFilename(filename, parent)
        msg = "Couldn't find markfile `{}`"
        raise MarkfileError(msg.format(filename))

    def get_source(self, environment, template):
        path = self.findFilename(template)
        if not os.path.exists(path):
            raise jinja2.TemplateNotFound(template)
        mtime = os.path.getmtime(path)
        with file(path) as f:
            source = f.read().decode('utf-8')
        return source, path, lambda: mtime == os.path.getmtime(path)

def makeEnvironment(strict=False, **kwargs):
    """
    Simple conveinence function for creating a Jinja2 Environment with
    a strict flag and some filters.
    """
    if strict:
        kwargs['undefined'] = jinja2.StrictUndefined

    env = jinja2.Environment(**kwargs)
    env.filters['popen'] = popen
    return env

def parseVariables(env, source):
    """
    Return the variables referenced in the source Jinja2 template string.
    """
    ast = env.parse(source)
    variables = list(meta.find_undeclared_variables(ast))
    return sorted(variables, cmp=lambda a,b: cmp(source.find(a), source.find(b)))

def drainParameters(variables, args, kwargs):
    """
    Attempt to satisfy all variables by consuming args and kwargs.
    """

    context = {}
    for name in variables:
        if args:
            context[name] = args.pop(0)
        elif kwargs and name in kwargs:
            context[name] = kwargs.pop(unicode(name))
    return context

def callTemplate(env, source, args, kwargs):
    """
    Attempt to render a template in strict-mode by utilizing args and kwargs for
    the context of the template. Variables not filled will raise a
    TemplateVariableError.

    Variables are referenced in the template with [ ] rather than {{ }}.
    """
    args, kwargs = list(args), dict(kwargs)
    variables = parseVariables(env, source)
    context = drainParameters(variables, args, kwargs)
    template = env.from_string(source)

    try:
        return template.render(**context)
    except jinja2.exceptions.UndefinedError as e:
        # extract the missing variable from the error message
        attribute = e.message.split()[0].replace("'", "")
        msg = "Template requires missing `{}` variable."
        error = TemplateVariableError(msg.format(attribute))
        error.variable = attribute
        raise error
