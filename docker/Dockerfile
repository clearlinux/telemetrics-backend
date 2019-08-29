# Copyright (C) 2018 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
FROM clearlinux:latest

ADD ./requirements.txt /tmp/requirements.txt
RUN swupd bundle-add sudo uwsgi nginx python-basic redis-native
RUN pip3 install -r /tmp/requirements.txt
