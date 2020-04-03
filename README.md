# telemetrics-backend

## Overview

This project provides the server-side component of a complete telemetrics
(telemetry + analytics) solution for Linux-based operating systems. The
client-side component source repository lives at
https://github.com/clearlinux/telemetrics-client.

It consists of a Flask application `telemetryui`,
that exposes several views to visualize the telemetry data. The `telemetryui`
app also provides a REST API to perform queries on the data.

The Flask apps have several dependencies listed [here](services/collector/requirements.txt)
and [here](deployments/services/telemetryui/requirements.txt). The testing infrastructure
is described by [this](deployments/docker-compose.yaml) docker-compose.yaml and production by
[this](deployments/docker-compose.prod.yaml) docker-compose.prod.yaml

## Security considerations

The telemetrics-backend was written with a particular deployment scenario in
mind: internal LAN (e.g. a corporate network not exposed to the public internet).
Also, no identity management, user authentication, or role-based access controls
have yet been implemented for the applications.

To control access to the applications, it is recommended that system
administrators leverage web server authentication.

To enable HTTPS connections replace the placeholders files [here](services/nginx/telemetry.cert.pem)
and [here](services/nginx/telemetry.key.pem) with a certificate and private key
for your server. In addition uncomment lines 3, 9, and 10 in the [sites](services/nginx/sites.conf).
configuration file.

## Deployment

The application is containerized to simplify the deployment. 

```
# checkout latest tag source
git clone --branch latest https://github.com/clearlinux/telemetrics-backend.git
cd telemetrics-backend
```

For a deployment in production make sure to update the value for POSTGRES_PASSWORD otherwise
the build step will fail.

```
# update services/production.env
vi services/production.env

# build production environment
sudo -E docker-compose --file ./deployments/docker-compose.prod.yaml build --force-rm
```

Once the images are build successfully the environment can be started using:

```
# start environment on the background
sudo -E docker-compose --file ./deployments/docker-compose.prod.yaml up --detach
```

### Deploying as systemd service

To deploy the environment as a systemd service use the following example:

```
[Unit]
Description=Telemetry Backend
Requires=docker.service
After=docker.service

[Service]
Restart=always
WorkingDirectory=/srv/telemetrics-backend
ExecStart=/usr/local/bin/docker-compose --file deployments/docker-compose.prod.yaml up
ExecStop=/usr/local/bin/docker-compose --file deployments/docker-compose.prod.yaml down -v

[Install]
WantedBy=multi-user.target
```


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

Any new migration from a new realease will be applied when the environment is
started, this applies for both production and testing configurations.

## Development

```
# Build
sudo -E docker-compose --file deployments/docker-compose.yaml build --force-rm

# Launch
sudo -E docker-compose --file deployments/docker-compose.yaml up
```

## Software License

The telemetrics-backend project is licensed under the Apache License, Version
2.0. The full license text is found in the LICENSE file, and individual source
files contain the boilerplate notice described in the appendix of the LICENSE
file.


## Security Disclosures

To report a security issue or receive security advisories please follow procedures
in this [link](https://01.org/security).
