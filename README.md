# mark

    "Hmm I'm not sure what's happening. Let me check mark."

    *cringe*


**mark** is a simple command-line utility for running **SQL queries** against a database of interest from a **templated YAML file**. Results are presented in simple **text-based graphs** or **tables**.


# Installation

mark can be **installed with pip**:

    $ pip install mark

Alternatively, by **cloning the source**:

    $ git clone https://github.com/dustinlacewell/mark.git
    $ cd mark && python setup.py install

Running the `mark` command **without a Markfile** will fail *but* confirms installation was a success:

    $ mark
    ✗ Error reading markfile: Couldn't find markfile `markfile.yml`

The `--help` flag shows a little more information:

    $ mark --help
    mark --help
    Usage: mark [OPTIONS] [QUERY]

    Options:
      -m, --markfile      file containing queries and db details
      -l, --list-queries  list available queries
      --help              Show this message and exit.

# Markfiles

Markfiles are [YAML documents](https://en.wikipedia.org/wiki/YAML) consisting of a **config section** and one or more **named query specifications**. The config section details how mark should **connect to the database**. The rest of the objects in the document describe named SQL queries and **how their results should be displayed**. Markfiles support [Jina2 templating](http://jinja.pocoo.org/docs/dev/) which allows for de-duplication of repeated SQL clauses, parametric queries, and interpolation of subprocess output.

## Markfile location

**By default** mark will look for `markfile.yml` to parse. This **can be changed** by passing the `-m/--markfile` flag. The filename should contain no absolute or relative path components.

Starting from the current working-directory, mark will recursively search parent directories until the named file is found if it exists.

## Database connection

Every Markfile must define a top-level object `config` which has the following attributes for specifying **how to connect to the database**:

    config:
      host: db.example.com
      port: 5432
      user: username
      pass: password
      name: database

## Query Specifications

**Every other top-level object** in the Markfile describes an SQL query and optionally how to graph the rows returned by executing it. In the simpliest case, the only attribute is `query` which specifies the raw SQL:

    errors:
      query: select error, count(*) from table_name group by error order by count

## Running queries

A `markfile.yml` with the following contents will allow us to run the query therein against our hypothetical database server:

    config:
      host: db.example.com
      port: 5432
      user: username
      pass: password
      name: database

    errors:
      query: select error, count(*) from table_name group by error order by count

The `errors` query can then be executed by invoking mark on the command-line and **providing the query name**. By default, the results will be displayed in a table format similar to using familiar command-line interactive database query tools:

    $ mark errors
    | error         | count   |
    |---------------+---------+
    |something bad! |        5|
    |the sky fell   |       24|
    |segfault       |        9|


## Listing Queries

Queries specified inside the Markfile can be listed by passing the `-l/--list-queries` flag:

    $ mark -l
    Available Queries in `/home/user/project/markfile.yml`
      errors

