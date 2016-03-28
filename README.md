Prometheus MySQL Exporter
====
This Prometheus exporter periodically runs configured queries against a MySQL database and exports the results as Prometheus gauge metrics.

# Installation
You will need Python 3, pip 3, and libmysqlclient-dev installed to run the exporter.

Run the following in the root project directory to install (i.e. download dependencies, create start script):
```
> pip3 install .
```
Note that you may need to add the start script location (see pip output) to your `PATH`.

# Usage
Once installed, you can run the exporter with the `prometheus-mysql-exporter` command.

By default, it will bind to port 8080, query MySQL on `localhost:3306` using the `root` user (with no password) and run queries configured in a file `exporter.cfg` in the working directory. There is no default database to run the queries on, so you must specify at least one. You can set the database(s) and change any defaults as required by passing in options:
```
> prometheus-mysql-exporter -p <port> -s <mysql server> -u <mysql username> -P <mysql password> -c <path to query config file> -d <mysql database(s)>
```
Run with the `-h` flag to see details on all the available options.

See the provided `exporter.cfg` file for query configuration examples and explanation.

# Docker
You can build a docker image using the provided Dockerfile. Run the following in the root project directory:
```
> sudo docker build -t prometheus-mysql-exporter .
```
To run a container successfully, you will need to mount a query config file to `/usr/src/app/exporter.cfg` and map container port 8080 to a port on the host. Any options placed after the image name (`prometheus-mysql-exporter`) will be passed to the process inside the container. You will also need to use this to configure the MySQL server using `-s`.
```
> sudo docker run --rm --name exporter \
    -v <path to query config file>:/usr/src/app/exporter.cfg \
    -p 8080:8080 \
    prometheus-mysql-exporter -s <mysql server> -d <mysql database(s)>
```
You can change other options in the same way as `-s`. For example, you could change where the query config file is read from using `-c`.

If you don't want to mount the query config file in at run time, you could modify the Dockerfile to copy it in when building the image.

# Development
The exporter can be installed in "editable" mode, using pip's `-e` flag. This allows you to test out changes without having to re-install.
```
> pip3 install -e .
```

Send me a PR if you have a change you want to contribute!
