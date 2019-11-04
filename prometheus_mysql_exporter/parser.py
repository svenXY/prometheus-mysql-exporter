from numbers import Number

from .metrics import format_metric_name, format_label_key, format_label_value


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
        labels = {'db': db_name}
        labels.update({column: str(row[column])
                       for column in row
                       if column not in value_columns})

        formatted_labels = {format_label_key(k): format_label_value(v)
                            for k, v in labels.items()}

        for value_column in value_columns:
            value = row[value_column]
            if isinstance(value, Number):
                result.append((
                    format_metric_name(query_name, value_column),
                    "Value column '{}' for query '{}'.".format(value_column, query_name),
                    formatted_labels,
                    value,
                ))

    return result
