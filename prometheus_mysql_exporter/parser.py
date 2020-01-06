from collections import OrderedDict
from numbers import Number

from .metrics import format_metric_name, format_labels


def parse_response(query_name, db_name, value_columns, response):
    """
    Parse a SQL query response into a list of metric tuples.

    Each value column in each row of the response results in a metric, so long
    it is numeric. Other columns are converted to labels. The db name is also
    included in the labels, as 'db'.

    Metric tuples contain:
    * metric name,
    * metric documentation,
    * dict of label key -> label value,
    * metric value.
    """
    result = []

    for row in response:
        # NOTE: This db label isn't strictly necessary, since a single query can
        #       only be run on a single database. It's retained for backwards
        #       compatibility with previous versions that allowed queries to be
        #       run on multiple databases.
        labels = OrderedDict({'db': db_name})
        labels.update((column, str(row[column]))
                      for column in row
                      if column not in value_columns)

        for value_column in value_columns:
            value = row[value_column]
            if isinstance(value, Number):
                result.append((
                    format_metric_name(query_name, value_column),
                    "Value column '{}' for query '{}'.".format(value_column, query_name),
                    format_labels(labels),
                    value,
                ))

    return result
