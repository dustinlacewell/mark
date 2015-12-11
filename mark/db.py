import psycopg2 as psql

import queries

class DBConfig(object):
    def __init__(self, host, port, username, password, database):
        self.host = host
        self.port = int(port)
        self.username = username
        self.password = password
        self.database = database

    @property
    def uri(self):
        return queries.uri(self.host, int(self.port),
                           self.database, self.username, self.password)

    def asDict(self):
        return {
            'host':self.host,
            'port':self.port,
            'user':self.username,
            'password':self.password,
            'database':self.database,
        }


class DBConnection(object):
    def __init__(self, db_config):
        self.config = db_config

    def execute(self, query, **kwargs):
        with queries.Session(self.config.uri) as session:
            return list(session.query(query, **kwargs))
