import argparse
import configparser
import json
import sched
import time
import MySQLdb

from prometheus_client import start_http_server, Gauge

from exporter.parser import parse_response

gauges = {}

def format_label_value(value_list):
    return '_'.join(value_list)

def format_metric_name(name_list):
    return '_'.join(name_list)

def update_gauges(metrics):
    metric_dict = {}
    for (name_list, label_dict, value) in metrics:
        metric_name = format_metric_name(name_list)
        if metric_name not in metric_dict:
            metric_dict[metric_name] = (tuple(label_dict.keys()), {})

        label_keys = metric_dict[metric_name][0]
        label_values = tuple([
            format_label_value(label_dict[key])
            for key in label_keys
        ])

        metric_dict[metric_name][1][label_values] = value

    for metric_name, (label_keys, value_dict) in metric_dict.items():
        if metric_name in gauges:
            (old_label_values_set, gauge) = gauges[metric_name]
        else:
            old_label_values_set = set()
            gauge = Gauge(metric_name, '', label_keys)

        new_label_values_set = set(value_dict.keys())

        for label_values in old_label_values_set - new_label_values_set:
            gauge.remove(*label_values)

        for label_values, value in value_dict.items():
            if label_values:
                gauge.labels(*label_values).set(value)
            else:
                gauge.set(value)

        gauges[metric_name] = (new_label_values_set, gauge)

def run_scheduler(scheduler, mysql_client, name, interval, query, value_columns):
    def scheduled_run(scheduled_time):
        try:
            cursor = mysql_client.cursor()
            cursor.execute(query)
            raw_response = cursor.fetchall()
        except Exception as ex:
            print('Error: ' + str(ex))
            pass
        else:
            columns = [column[0] for column in cursor.description]
            response = [{column: row[i] for i, column in enumerate(columns)} for row in raw_response]

            metrics = parse_response(value_columns, response, [name])
            update_gauges(metrics)
        finally:
            cursor.close()

        next_scheduled_time = scheduled_time + interval
        scheduler.enterabs(
            next_scheduled_time,
            1,
            scheduled_run,
            (next_scheduled_time,)
        )

    next_scheduled_time = time.monotonic()
    scheduler.enterabs(
        next_scheduled_time,
        1,
        scheduled_run,
        (next_scheduled_time,)
    )

def main():
    parser = argparse.ArgumentParser(description='Export MySQL query results to Prometheus.')
    parser.add_argument('-s', '--mysql-server', default='localhost',
        help='address of a MySQL server to run queries on. A port can be provided if non-standard (3306) e.g. mysql:3333 (default: localhost)')
    parser.add_argument('-p', '--port', type=int, default=8080,
        help='port to serve the metrics endpoint on. (default: 8080)')
    parser.add_argument('-c', '--config-file', default='exporter.cfg',
        help='path to query config file. Can be absolute, or relative to the current working directory. (default: exporter.cfg)')
    parser.add_argument('-u', '--mysql-user', default='root',
        help='MySQL user to run queries as. (default: root)')
    parser.add_argument('-P', '--mysql-password', default='',
        help='password for the MySQL user, if required. (default: no password)')
    args = parser.parse_args()

    port = args.port
    if ':' in args.mysql_server:
        mysql_host, mysql_port = args.mysql_server.split(':', 1)
    else:
        mysql_host = args.mysql_server
        mysql_port = 3306

    username = args.mysql_user
    password = args.mysql_password

    config = configparser.ConfigParser()
    config.read(args.config_file)

    query_prefix = 'query_'
    queries = {}
    for section in config.sections():
        if section.startswith(query_prefix):
            query_name = section[len(query_prefix):]
            query_interval = config.getfloat(section, 'QueryIntervalSecs')
            query = config.get(section, 'QueryStatement')
            value_columns = config.get(section, 'QueryValueColumns').split(',')

            queries[query_name] = (query_interval, query, value_columns)

    scheduler = sched.scheduler()

    print('Starting server...')
    start_http_server(port)
    print('Server started on port {}'.format(port))

    for name, (interval, query, value_columns) in queries.items():
        mysql_client = MySQLdb.connect(
            host = mysql_host,
            port = mysql_port,
            user = username,
            passwd = password,
        )
        run_scheduler(scheduler, mysql_client, name, interval, query, value_columns)

    try:
        scheduler.run()
    except KeyboardInterrupt:
        pass

    print('Shutting down')
