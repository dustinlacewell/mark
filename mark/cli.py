# -*- coding: utf-8 -*-

import yaml

import click

from blessings import Terminal
t = Terminal()

from mark.template import makeEnvironment, MarkfileLoader
from mark.query import callQuery, parseQueryColumns, printQueryTable
from mark.graph import graphs, TableGraph
from mark.db import DBConfig, DBConnection
from mark.utils import parseArgumentCall
from mark.errors import MarkError, CLIError, MarkfileError, QueryError, TemplateVariableError

def getMarkFile(markfile, **kwargs):
    """
    Search for the specified Markfile and load it as a Jinja2 template. Return the
    result parsed as YAML along with the filename.
    """
    try:
        # the MarkfileLoader will recursively search parent directories
        # for the named template file
        env = makeEnvironment(loader=MarkfileLoader())
        t = env.get_template(markfile)
        r = t.render() # no external context is needed
        return t.filename, yaml.load(r)
    except IOError:
        msg = "Markfile `{}` could not be found."
        raise CLIError(msg.format(markfile))
    except Exception as e:
        msg = "Error reading markfile: {}"
        raise CLIError(msg.format(str(e)))

def getSpec(markfile, name):
    """
    Return the named query-specification from the markfile other raise a CLIError.
    """
    if name not in markfile:
        msg = "Query `{}` was not found in markfile."
        raise CLIError(msg.format(name))
    return markfile[name]

def getQuery(spec, name, args, kwargs):
    """
    Parse and render the query-specification using the provided args and kwargs
    as context for the rendering. If all required variables in the query are
    not provided raise a QueryError.
    """

    if 'query' not in spec:
        msg = "Query `{}` contains no `query` field."
        raise QueryError(msg.format(name))

    try:
        # render the query template using the args and kwargs
        query_template = spec['query']
        query = callQuery(query_template, args, kwargs)
    except TemplateVariableError as e:
        # the args and kwargs were not sufficient to satisfy all
        # required parameters of the query
        msg = "Query `{}` requires missing `{}` parameter."
        raise QueryError(msg.format(name, e.variable))
    return query

def getGraph(name, spec, fields):
    """
    Get a graph instance based on the details in the spec and the provided list of
    column field names.
    """

    if 'graph' not in spec:
        return TableGraph(fields, tablefmt='orgtbl')
    graph_info = spec['graph']

    if 'type' not in graph_info:
        msg = "`Query `{}` does not specify graph type."
        raise QueryError(msg.format(name))

    # the name of the type of graph
    graph_type = graph_info.pop('type')
    if graph_type not in graphs:
        msg = "`{}` is not a valid graph type for query `{}`"
        raise QueryError(msg.format())

    # get the specified graph class and return an instance
    graph_cls = graphs[graph_type]
    return graph_cls(fields, **graph_info)

def getDBConfig(markfile):
    """
    Return an object from the markfile describing how to connect to the remote
    database.
    """
    if 'config' not in markfile:
        msg = "Markfile is missing `config` section."
        raise MarkfileError(msg)
    config = markfile['config']
    args = []
    for attr in ('host', 'port', 'user', 'pass', 'name'):
        if attr not in config:
            msg = "Markfile `config` section has no `{}` key."
            raise MarkfileError(msg.format(attr))
        args.append(config[attr])
    return DBConfig(*args)

class LazyString(basestring):
    def __init__(self, partial):
        basestring.__init__(self, "")
        self.partial = partial
        self.value = ""

    def __str__(self):
        if not self.value:
            self.value = self.partial()

@click.command()
@click.option('--markfile', '-m', default='markfile.yml',
              help="file containing queries and db details")
@click.option('--list-queries', '-l', is_flag=True,
              help="list available queries")
@click.argument('query', required=False)
def cli(list_queries, query, **kwargs):
    # get the renderered markfile
    filename, markfile = getMarkFile(**kwargs)

    # print queries and quit if -l is passed
    if list_queries:
        markfile.pop('config')
        printQueryTable(filename, markfile)
        return

    # parse the query call from the command-line
    query_name, query_args, query_kwargs = parseArgumentCall(query)
    # get the named query-specification
    spec = getSpec(markfile, query_name)
    # get a Query instance based on the query call
    query = getQuery(spec, query_name, query_args, query_kwargs)
    # get the selected column names from the query
    columns = parseQueryColumns(query)
    # get a graph instance based on the query-specification
    graph = getGraph(query_name, spec, columns)
    # establish a connection to the database
    db_config = getDBConfig(markfile)
    db = DBConnection(db_config)
    # execute the final query sql
    rows = db.execute(query)
    if rows: # print the graphed results
        print t.bold_white(query_name).encode('utf8', 'replace')
        print graph.render(rows).encode('utf8', 'replace')
    else: # alert that no results were returned
        msg = "Query `{}` returned no results."
        print t.yellow(msg.format(query_name))

def main():
    try:
        cli()
    except MarkError as e:
        print u" {} {}".format(t.red(u"✗ "), unicode(e)).encode('utf8')
