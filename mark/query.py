from collections import defaultdict

import sqlparse

from blessings import Terminal
t = Terminal()

from mark.template import callTemplate, makeEnvironment, parseVariables
from mark.errors import QueryError
from mark.utils import pad

# template helpers
def createQueryEnvironment():
    """
    Create a Jinja2 Environment suitable for rendering query templates.
    """
    return makeEnvironment(strict=True,
                           variable_start_string="[",
                           variable_end_string="]")

def extractQueryParams(query):
    """
    Extract Jijna2 variables from a query template.
    """
    env = createQueryEnvironment()
    return parseVariables(env, query)

def queryParametersFromMapping(mapping):
    """
    Take a dictionary mapping named query templates. For
    each template, parse out the referenced template
    variables. Return a list of tuples for each query name
    and its associated template variables.

    Example:
    {'query_a': sql_query} => [('query_a', var1, var2, var3)]
    """
    rows = []
    env = createQueryEnvironment()
    for key in sorted(mapping.keys(), key=len):
        spec = mapping[key]
        columns = parseVariables(env, spec['query'])
        rows.append([key] + columns)
    return rows

def indexedLengthMaximums(rows):
    """
    Take a list of tuples. For each tuple, compare the
    length of the item at each index against the maximum
    length for the same index in other tuples. Return a
    dictionary mapping tuple index to maximum length.

    Example:
    [('a', 'bbb'), ('aa', 'b')] => {0:2, 1:3}
    """
    lengths = defaultdict(lambda: 0)
    for row in rows:
        for idx, value in enumerate(row):
            length = len(value)
            if lengths[idx] < length:
                lengths[idx] = length
    return lengths

def printQueryTable(filename, markfile):
    """
    Print each query in the markfile by name and
    arguments. Laboriously, Format the output into a table
    so that arguments take up the same width for
    readability.
    """

    # get a list of each query template and associated variables
    queries = queryParametersFromMapping(markfile)
    # sort the queries by how many parameters it takes
    queries = sorted(queries, key=len)
    # get an index of the maximum lengths of query names and variables
    indexed_lengths = indexedLengthMaximums(queries)
    print t.bold("Available Queries in `{}`".format(filename))
    for query in queries:
        name, parameters = query[0], query[1:]
        # print the query name
        print "{}".format(pad(name, indexed_lengths[0], '>')),
        # and each parameter
        for idx, value in enumerate(parameters):
            field_width = indexed_lengths[idx + 1]
            padded_field = pad(value, field_width, '^')
            print "[{}]".format(padded_field),
        # print newline for next query
        print ""


# sql helpers

def parseQueryTokens(sql):
    """
    Parse an SQL query into an AST of tokens.
    """
    statement = sqlparse.parse(sql)[0]
    stripped = [sqlparse.tokens.Whitespace]
    return [t for t in statement.tokens if t.ttype not in stripped]


def assertSelectQuery(query_tokens):
    """
    Assert provided AST tokens represent a SELECT query.
    """
    type_token = query_tokens[0]

    if type_token.ttype != sqlparse.tokens.DML \
       or not type_token.value == u'select':
        msg = "Only 'select' queries are allowed."
        raise QueryError(msg)


def assertQueryColumns(query_tokens):
    """
    Assert provided AST tokens begin with column names to select.
    """
    ident_token = query_tokens[1]

    if not isinstance(ident_token, sqlparse.sql.IdentifierList):
        msg = "Query must begin with column names to select."
        raise QueryError(msg)


def parseQueryColumns(sql):
    """
    Extract the column identifiers selected in the provided query.
    """
    query_tokens = parseQueryTokens(sql)
    assertSelectQuery(query_tokens)
    assertQueryColumns(query_tokens)

    identifiers = []
    ident_token = query_tokens[1]
    for token in ident_token.tokens:
        if isinstance(token, (sqlparse.sql.Identifier,
                              sqlparse.sql.Function)):
            identifiers.append(token.get_name())
        elif token.ttype == sqlparse.tokens.Keyword:
            identifiers.append(token.value)

    if not identifiers:
        msg = "No columns are selected in query."
        raise QueryError(msg)

    return identifiers

def callQuery(query, args, kwargs):
    env = createQueryEnvironment()
    return callTemplate(env, query, args, kwargs)
