Prometheus MySQL Exporter
====
This Prometheus exporter periodically runs configured queries against a MySQL server and exports the results as Prometheus gauge metrics.

[Source Code](https://github.com/braedon/prometheus-mysql-exporter) | [Python Package](https://pypi.org/project/prometheus-mysql-exporter) | [Docker Image](https://hub.docker.com/r/braedon/prometheus-mysql-exporter) | [Helm Chart](https://braedon.github.io/helm/prometheus-mysql-exporter)

# Installation
The exporter requires Python 3 and Pip 3 to be installed.

To install the latest published version via Pip, run:
```bash
> pip3 install prometheus-mysql-exporter
```
Note that you may need to add the start script location (see pip output) to your `PATH`.

# Usage
Once installed, you can run the exporter with the `prometheus-mysql-exporter` command.

By default, it will bind to port 9207, query MySQL on `localhost:3306` using the `root` user (with no password) and run queries configured in a file `exporter.cfg` in the working directory. You can change any defaults or other settings as required by passing in options:
```bash
> prometheus-mysql-exporter -p <port> -s <mysql server> -u <mysql username> -P <mysql password> -z <local timezone> -c <path to query config file>
```
Run with the `-h` flag to see details on all the available options.

Note that all options can be set via environment variables. The environment variable names are prefixed with `MYSQL_EXPORTER`, e.g. `MYSQL_EXPORTER_MYSQL_USER=fred` is equivalent to `--mysql-user fred`. CLI options take precidence over environment variables.

Command line options can also be set from a configuration file, by passing `--config FILE`. The format of the file should be [Configobj's unrepre mode](https://configobj.readthedocs.io/en/latest/configobj.html#unrepr-mode), so instead of `--mysql-user fred` you could use a configuration file `config_file` with `mysql-user="fred"` in it, and pass `--config config_file`. CLI options and environment variables take precedence over configuration files.

CLI options, environment variables, and configuration files all override any default options. The full resolution order for a given option is: CLI > Environment > Configuration file > Default.

See the provided [exporter.cfg](exporter.cfg) file for query configuration examples and explanation.

# Docker
Docker images for released versions can be found on Docker Hub (note that no `latest` version is provided):
```bash
> sudo docker pull braedon/prometheus-mysql-exporter:<version>
```
To run a container successfully, you will need to mount a query config file to `/usr/src/app/exporter.cfg` and map container port 9207 to a port on the host. Any options placed after the image name (`prometheus-mysql-exporter`) will be passed to the process inside the container. For example, you will need to use this to configure the MySQL server using `-s`.
```bash
> sudo docker run --rm --name exporter \
    -v <path to query config file>:/usr/src/app/exporter.cfg \
    -p <host port>:9207 \
    braedon/prometheus-mysql-exporter:<version> -s <mysql server>
```
If you don't want to mount the query config file in at run time, you could extend an existing image with your own Dockerfile that copies the config file in at build time.

# Helm
A Helm chart is available from the Helm repo at [https://braedon.github.io/helm](https://braedon.github.io/helm/).
```bash
> helm repo add braedon https://braedon.github.com/helm
> helm repo update

> helm install braedon/prometheus-mysql-exporter --name <release name> \
                                                 --set mysql.server=<mysql server address> \
                                                 --set image.tag=<image tag>
```
See the [`prometheus-mysql-exporter` chart README](https://braedon.github.io/helm/prometheus-mysql-exporter/) for more details on how to configure the chart.

# Development
To install directly from the git repo, run the following in the root project directory:
```bash
> pip3 install .
```
The exporter can be installed in "editable" mode, using pip's `-e` flag. This allows you to test out changes without having to re-install.
```bash
> pip3 install -e .
```
To build a docker image directly from the git repo, run the following in the root project directory:
```bash
> sudo docker build -t <your repository name and tag> .
```
Send me a PR if you have a change you want to contribute!
