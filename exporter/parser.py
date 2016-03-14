def parse_response(value_columns, response, metric=[], labels={}):
    result = []

    for row in response:
      result_labels = {column: (str(row[column]),) for column in row if column not in value_columns}
      final_labels = labels.copy()
      final_labels.update(result_labels)
      for value_column in value_columns:
        result.append((metric + [value_column], final_labels, row[value_column]))

    return result
