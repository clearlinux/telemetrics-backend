# telemetrics-backend

## Overview

This project provides the server-side component of a complete telemetrics
(telemetry + analytics) solution for Linux-based operating systems. The
client-side component source repository lives at
https://github.com/clearlinux/telemetrics-client.

It consists of a Flask application `telemetryui`,
that exposes several views to visualize the telemetry data. The `telemetryui`
app also provides a REST API to perform queries on the data.

The applications run within a web stack, using the nginx web server, the uWSGI
application server, and PostgreSQL as the underlying database server.

The Flask apps have several other dependencies and are listed below.

* SQLAlchemy - for performing queries on the PostgreSQL database
* Flask-SQLAlchemy - for SQLAlchemy integration with Flask
* WTForms - for HTML form validation and rendering
* Flask-WTF - for WTForms integration with Flask
* alembic - for performing database migrations
* Flask-Migrate - for alembic integration with Flask
* Jinja2 - templating engine used by Flask
* Bootstrap - for styling of Jinja2 templates
* jQuery - for client-side scripting in templates
* Chart.js - for rendering of charts in templates

## Security considerations

The telemetrics-backend was written with a particular deployment scenario in
mind: single server/VM hosting and running on an internal LAN (e.g. a corporate
network not exposed to the public internet). Also, no identity management, user
authentication, or role-based access controls have yet been implemented for the
applications.

To control access to the applications, it is recommended that system
administrators leverage web server authentication.

Regarding alternate deployment scenarios, one might want to host the telemetryui
and database on three separate servers/VMs; and implement network
access controls for these systems. The in-tree deployment script does not
support these types of deployments, but with minimal modification to the
source, they should be possible.

## Installation

To install the telemetrics-backend, a deployment/installation script is
provided that auto-installs required dependencies for the applications,
configures nginx and uwsgi, deploys snapshots of the applications, and starts
all required services. The script is named `deploy.sh` and lives in the
scripts/ directory in this repository.

The script supports installation to the following Linux distributions: Ubuntu
Server 16.04 (or newer), and Clear Linux OS for Intel Architecture (any recent
build).

### Running the deployment script

To see all options, run:

```
$ cd scripts
$ ./deploy.sh -h
```

#### Prerequisites

* Copy the deploy.sh script to the system where you will be installing
  telemetrics-backend (e.g. using `scp`). Remote installations are not yet
  supported.

* On Ubuntu Server, make sure you `apt-get update` before continuing.

* Install `sudo` if needed, and add your user to sudoers.

* Set the `https_proxy` variable in the shell environment if your system is
  behind a proxy.

#### Installation

To perform a fresh installation on Ubuntu Server, run the following locally on
the system:

```
$ ./deploy.sh -H localhost -a install
```

If you are installing on Clear Linux OS, run:

```
$ ./deploy.sh -H localhost -d clr -a install
```

#### Installation Notes

During script execution, you will be prompted for user input:

* The first prompt begins with "DB password:", asking for a password to set for
  the `telemetry` database. If you do not enter a value before pressing ENTER,
  the password will be `postgres`.

* If your sudo access requires a password, you will be prompted for that
  password in the course of the installation.

* When installing to Clear Linux OS, you will be prompted to enter a password
  for the `postgres` user account. This is necessary because Clear Linux OS by
  default ships with a `postgres` system account, not a user account. Thus the
  script modifies the account and requires a password set to properly configure
  PostgreSQL.

When the installation is complete, you will see the following message:

```
Install complete (installation folder: /var/www/telemetry)
```

#### Other options

Other useful options for `deploy.sh` include `-r` and `-s`. The `-r` option
sets the location for the telemetrics-backend git source repository you are
working with. Its default value is the upstream repo location on
github.com/clearlinux. The `-s` option lets you select a different git branch
to install/deploy from rather than "master", the default value.

## `telemetryui` views

The `telemetryui` app is a web app that exposes several views to visualize the
telemetry data and also provides a REST API to perform queries on record data.

The current views are:

* Records view - a paginated list of all records in the `telemetry` database that
  have been accepted by the `collector`. The records are presented in tabular
  format and the columns map to select fields from the `records` database table.
  At the top of the view, an HTML form can be used for "advanced searches",
  filtering the list of records to display.

* Builds view - a basic column chart that displays how many records have been
  received for each OS build. Note that the view is optimized for Clear Linux
  OS, since the chart only displays data for records when their build numbers are
  integers. For example, records with non-integer build numbers, like "16.04" for
  Ubuntu, are not displayed in this view.

* Stats view - two pie charts displaying the statistical breakdown of
  classifications and platforms for all records in the database. The
  "classification" field is used to identify the type of record sent by a
  specific client probe; classifications use the format DOMAIN/PROBE/REST, where
  DOMAIN is the vendor of the probe, PROBE is the probe name, and REST is a
  probe-defined field to classify what is contained in the payload. The
  "platform" field is a formatted string,
  `"sys_vendor|product_name|product_version"`, where the values are taken from
  files with those names in the `/sys/class/dmi/id/` directory; if any of these
  files are empty or contain only space characters, the client library
  substitutes "blank" for their value.

* Crashes view - features a table displaying the top 10 crash reports from
  crash records received in the past week. It only consumes records from the
  telemetrics-client `crashprobe`, which extracts backtrace information from core
  files and creates/sends telemetry records containing this data. The crash
  reports are grouped by "guilties"; a guilty is a frame from a crash backtrace
  chosen as the best candidate for the cause of the crash. The logic for
  determining crash record guilty frames accepts user input; the user can
  identify which frames in a backtrace are never guilty.

* MCE view - charts that display MCE (machine check exception) data from a
  patched version of `mcelog` that uses libtelemetry to create and send
  telemetry records. The mcelog patch is available from
  https://github.com/clearlinux-pkgs/mcelog.

* Thermal view - similar to the MCE view, but it only displays a chart for MCE
  Thermal event records, also received from the patched `mcelog`.

* Updates view - displays a [SWUPD](https://github.com/clearlinux/swupd-client)
  update matrix, which lists the total number of successful SWUPD updates of
  the Clear Linux OS from build versions listed in the first column to build
  versions listed in the top row. The rightmost column and bottommost row list
  the total of updates from or to each version, respectively. The update
  statistics are received from the
  [swupd-probe](https://github.com/clearlinux/swupd-probe), which monitors the
  `/var/lib/swupd/telemetry` directory for files created by SWUPD that describe
  certain software update events, or other events of interest (a user adds a
  bundle, runs `swupd verify --fix`, etc).

* Population view - contains column charts that display the number of unique
  systems that are running each version of an OS over a specific range of time.
  The "uniqueness" of a system is determined by its "machine ID" field, managed
  by the telemetrics-client daemon, which by default rotates the value every 3
  days. Thus, the analysis presented in this view is *fuzzy* due to the machine
  ID rotation.

## Custom `telemetryui` views

To provided users with an extensible framework a concept of "plugin views" was
implemented to add views without the need to make changes to the core of the
application. To read more about [plugin view](/telemetryui/telemetryui/plugins/README.md)
go to relevant documentation.


## Special configuration

### Configuring nginx for TLS

The `sites_nginx.conf` config file is already enabled to accept TLS connections
on port 443. However, you must install the X509 certificate chain and the
certificate private key to a specific location before running `deploy.sh`. Both
files should be in PEM format. Additional details on specific considerations
can be found in the [nginx documentation](https://nginx.org/en/docs/http/configuring_https_servers.html).

The certificate chain must be installed to `/etc/nginx/ssl/telemetry.cert.pem`
and the private key installed to `/etc/nginx/ssl/telemetry.key.pem`.

If the certificates are not preinstalled, the `deploy.sh` script will simply
comment out TLS-related nginx configuration. Specifically, it will comment out
the `listen 443 ssl`, `ssl_certificate`, `ssl_certificate_key`,
`ssl_protocols`, and `ssl_ciphers` directives.

## Using the REST API

A REST API for querying records is available at "/api/records". The API returns
a JSON response that contains a list of records keyed on "records".

Several parameters are available for filtering queries, similar to the filters
available through the `telemetryui` Records view.

* `classification`: The classification of the record. Right now this is
  restricted at 140 characters. If a classification with more that 140
  characters is supplied as a query parameter, an HTTP response 400 is sent back.
* `severity`: The severity of the record. Restricted to integer value.
* `machine_id`: The id of the machine where this record was generated on.
  Should be 32 characters in length.
* `build`: The build on which the record was generated. Restricted to 256
  characters.
* `created_in_days`: This should be an integer value. It causes the query to
  return records created after the last given days. Note: the server timestamp
  is used as a reference point.
* `created_in_sec`: This should be an integer again. If returns the records
  created after the last given seconds. This is used only if the previous
  parameter is absent. Note: the server timestamp is used as a reference point.
* `limit`: The maximum number of records to be returned.

### Example queries

To query for records, simply make a GET call to the endpoint.

* `GET /api/records` - Returns a maximum of 10000 most recent records in the
  backend database ordered by the record id (descending).
* `GET /api/records?classification=org.clearlinux%2Fkernel%2Fwarning&severity=2&build=2980&created_in_sec=5&limit=100` - Returns at most 100 records with the classification
  "org.clearlinux/kernel/warning", severity 2, build 2980, and created in the
  last 5 seconds. As shown the query parameters need to be [URL encoded](https://en.wikipedia.org/wiki/Percent-encoding).

### Response object

The response is a JSON object that contains a list of objects keyed on
"records". This list is empty in case no records match the query parameters.
Example response:

```
{
    "records": [
        {
            "arch": "x86_64",
            "build": "2980",
            "classification": "org.clearlinux/hello/world",
            "kernel_version": "4.2.0-120",
            "machine_id": "66c196ce4222dd761470da5e7e35f6f1",
            "machine_type": "blank|blank|blank",
            "payload": "hello\n\n",
            "record_format_version": 2,
            "severity": 1,
            "ts_capture": "2015-09-30 00:39:35 UTC",
            "ts_reception": "2015-09-30 00:56:59 UTC"
        },
        {
            "arch": "x86_64",
            "build": "2980",
            "classification": "org.clearlinux/hello/world",
            "kernel_version": "4.2.0-120",
            "machine_id": "66c196ce4222dd761470da5e7e35f6f1",
            "machine_type": "blank|blank|blank",
            "payload": "hello\n",
            "record_format_version": 2,
            "severity": 1,
            "ts_capture": "2015-09-30 00:36:22 UTC",
            "ts_reception": "2015-09-30 00:38:45 UTC"
        }
    ]
}
```

## Creating new database migrations

Database migrations are managed using
[Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/). Upon initial
install of telemetrics-backend, the first migration will be applied, and any
additional migrations in the `telemetryui/migrations/versions/` directory will
be applied in sequence and upgrade the `telemetry` schema to the latest version.

To create a new migration, you can follow the steps below:

1. Deploy telemetrics-backend from a git topic branch (not production).
2. On the system deployed to, run

```
sudo su
cd /var/www/telemetry/
```

3. Modify `shared/model.py` as needed to make changes to the associated
   database schema.
4. When finished, create a migration with

```
cd telemetryui
source ../venv/bin/activate
export FLASK_APP=run.py
flask db migrate
```
5. The last command above will report the name of the new (autogenerated)
   migration file.  Modify it if additional migration steps are necessary
   beyond what Flask-Migrate autogenerated for you. To apply the migration
   to the database you need to execute the following command:
```
flask db upgrade
```

6. Copy the new file back to your git repository (into the
   `telemetryui/migrations/versions` directory), push it to your topic branch,
   and redeploy to test the new migration.

## Software License

The telemetrics-backend project is licensed under the Apache License, Version
2.0. The full license text is found in the LICENSE file, and individual source
files contain the boilerplate notice described in the appendix of the LICENSE
file.


## Security Disclosures

To report a security issue or receive security advisories please follow procedures
in this [link](https://01.org/security).
