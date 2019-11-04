import argparse
import configparser
import logging
import sched
import signal
import sys
import time
import MySQLdb

from jog import JogFormatter
from prometheus_client import start_http_server, Gauge

from prometheus_mysql_exporter.parser import parse_response

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


def run_scheduler(scheduler, mysql_client, dbs, name, interval, query, value_columns):
    def scheduled_run(scheduled_time):
        all_metrics = []

        for db in dbs:
            mysql_client.select_db(db)
            with mysql_client.cursor() as cursor:
                try:
                    cursor.execute(query)
                    raw_response = cursor.fetchall()

                    columns = [column[0] for column in cursor.description]
                    response = [{column: row[i] for i, column in enumerate(columns)} for row in raw_response]

                    metrics = parse_response(value_columns, response, [name], {'db': [db]})
                except Exception:
                    logging.exception('Error while querying db [%s], query [%s].', db, query)
                else:
                    all_metrics += metrics

        update_gauges(all_metrics)

        current_time = time.monotonic()
        next_scheduled_time = scheduled_time + interval
        while next_scheduled_time < current_time:
            next_scheduled_time += interval

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


def shutdown():
    logging.info('Shutting down')
    sys.exit(1)


def signal_handler(signum, frame):
    shutdown()


def main():
    signal.signal(signal.SIGTERM, signal_handler)

    def server_address(address_string):
        if ':' in address_string:
            host, port_string = address_string.split(':', 1)
            try:
                port = int(port_string)
            except ValueError:
                msg = "port '{}' in address '{}' is not an integer".format(port_string, address_string)
                raise argparse.ArgumentTypeError(msg)
            return (host, port)
        else:
            return (address_string, 3306)

    parser = argparse.ArgumentParser(description='Export MySQL query results to Prometheus.')
    parser.add_argument('-p', '--port', type=int, default=9207,
                        help='port to serve the metrics endpoint on. (default: 9207)')
    parser.add_argument('-c', '--config-file', default='exporter.cfg',
                        help='path to query config file. Can be absolute, or relative to the current working directory. (default: exporter.cfg)')
    parser.add_argument('-s', '--mysql-server', type=server_address, default='localhost',
                        help='address of a MySQL server to run queries on. A port can be provided if non-standard (3306) e.g. mysql:3333 (default: localhost)')
    parser.add_argument('-d', '--mysql-databases', required=True,
                        help='databases to run queries on. Database names should be separated by commas e.g. db1,db2.')
    parser.add_argument('-u', '--mysql-user', default='root',
                        help='MySQL user to run queries as. (default: root)')
    parser.add_argument('-P', '--mysql-password', default='',
                        help='password for the MySQL user, if required. (default: no password)')
    parser.add_argument('-j', '--json-logging', action='store_true',
                        help='turn on json logging.')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='detail level to log. (default: INFO)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='turn on verbose (DEBUG) logging. Overrides --log-level.')
    args = parser.parse_args()

    log_handler = logging.StreamHandler()
    log_format = '[%(asctime)s] %(name)s.%(levelname)s %(threadName)s %(message)s'
    formatter = JogFormatter(log_format) if args.json_logging else logging.Formatter(log_format)
    log_handler.setFormatter(formatter)

    log_level = getattr(logging, args.log_level)
    logging.basicConfig(
        handlers=[log_handler],
        level=logging.DEBUG if args.verbose else log_level
    )
    logging.captureWarnings(True)

    port = args.port
    mysql_host, mysql_port = args.mysql_server

    dbs = args.mysql_databases.split(',')

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

    for name, (interval, query, value_columns) in queries.items():
        mysql_client = MySQLdb.connect(host=mysql_host,
                                       port=mysql_port,
                                       user=username,
                                       passwd=password,
                                       autocommit=True)
        run_scheduler(scheduler, mysql_client, dbs, name, interval, query, value_columns)

    logging.info('Starting server...')
    start_http_server(port)
    logging.info('Server started on port %s', port)

    try:
        scheduler.run()
    except KeyboardInterrupt:
        pass

    shutdown()
