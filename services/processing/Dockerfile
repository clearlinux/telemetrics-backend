# Copyright (C) 2020 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
FROM clearlinux:latest

WORKDIR /srv/processing

RUN swupd bundle-add python3-basic
RUN mkdir -p /srv/processing
COPY ./processing .
COPY ./services/processing/. .
RUN pip3 install -r requirements.txt
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /srv/processing

USER appuser

CMD ["process.py", "ProcessCrashes", "--local-scheduler"]
