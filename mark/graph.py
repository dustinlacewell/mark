import itertools, re
from collections import defaultdict

from tabulate import tabulate

from mark.sparkline import sparkify
from mark.errors import QueryError

ansi_escape = re.compile(r'(\x1b[^m]*m)|\n|\t')

class TableGraph(object):
    def __init__(self, fields, **kwargs):
        # self.fields = fields
        self.fields = None
        self.kwargs = kwargs

    def render(self, rows):
        table = tabulate(rows, headers='keys', **self.kwargs)
        return u"{}\n{} rows".format(table, len(rows)).encode('utf8')

class SparkGraph(object):
    def __init__(self, fields, axis, minimum=None, maximum=None):
        if len(fields) != 2:
            msg = "SparkGraph can only process two-column queries."
            raise QueryError(msg)

        if axis not in fields:
            msg = "Axis `{}` not in query columns: {}"
            raise QueryError(axis, fields)

        self.fields = fields
        self.axis = axis
        self.label = [f for f in fields if f != axis][0]
        self.minimum = minimum
        self.maximum = maximum

    def render(self, rows):
        values = [r[self.axis] for r in rows]
        series = sparkify(values)
        labels = [r[str(self.label)] for r in rows]
        return tabulate([series, values], headers=labels)

class HistGraph(object):
    def __init__(self, fields, axis, minimum=None, maximum=None):
        if len(fields) != 2:
            msg = "HistGraph can only process two-column queries."
            raise QueryError(msg)
        if axis not in fields:
            msg = "Axis `{}` not in query columns: {}"
            raise QueryError(msg.format(axis, fields))

        self.fields = fields
        self.axis = axis
        self.minimum = minimum
        self.maximum = maximum

class MultiSparkGraph(object):
    def __init__(self, fields, partition, axis, minimum=None, maximum=None):
        self.fields = fields
        self.partition = partition
        self.axis = axis
        self.label = [f for f in fields if f not in (axis, partition)][0]
        self.minimum = minimum
        self.maximum = maximum

    def buildPartitions(self, rows):
        partitions = defaultdict(dict)
        for row in rows:
            index = row.pop(self.partition)
            index = ansi_escape.sub('', index)
            key = unicode(row.pop(self.label)).encode('ascii', 'replace')
            key = ansi_escape.sub('', key)
            value = row.pop(self.axis)
            partitions[index][key] = value
        superset = set(itertools.chain.from_iterable(partitions.values()))
        superset = sorted(list(superset))
        print superset
        for partition, dataset in partitions.items():
            for key in superset:
                dataset.setdefault(key, 0)
        return superset, partitions

    def render(self, rows):
        keys, partitions = self.buildPartitions(rows)
        results = []
        for partition, dataset in partitions.items():
            values = [dataset[k] for k in keys]
            series = sparkify(values)
            results.append((partition, series, max(values), sum(values)))
        results = sorted(results, cmp=lambda a,b: cmp(a[3], b[3]))
        return tabulate(results, headers=(self.partition, self.axis, 'peak', 'total'))

graphs = {
    'table': TableGraph,
    'spark': SparkGraph,
    'multispark': MultiSparkGraph,
}
