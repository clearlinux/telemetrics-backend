#
# Copyright 2015-2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
from time import (
    time,
    strftime,
    localtime)


def timesince(dt, default="just now"):
    now = time()
    diff = int(now - dt)

    months = diff // (86400 * 30)
    diff = diff % (86400 * 30)
    days = diff // 86400
    diff = diff % 86400
    hours = diff // 3600
    diff = diff % 3600
    minutes = diff // 60
    diff = diff % 60
    seconds = diff

    periods = (
        (months, "month", "months"),
        (days, "day", "days"),
        (hours, "hour", "hours"),
        (minutes, "minute", "minutes"),
        (seconds, "second", "seconds"),
    )

    for period, singular, plural in periods:
        if period:
            return "{} {} ago".format(period, singular if period == 1 else plural)

    return default


def local_datetime_since(sec):
    return strftime("%a, %d %b %Y %H:%M:%S", localtime(sec))


def basename(path):
    return os.path.basename(path)


def plugin_metadata(name):
    return name.title()

# vi: ts=4 et sw=4 sts=4
