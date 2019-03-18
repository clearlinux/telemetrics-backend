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

'''
Filename: src/log.c
Line: 641
Humanstring: "Successful verify"
version: 1640
runtime: 1057.548


Filename: src/log.c
Line: 615
Humanstring: "Successful update"
from_version: 1650
to_version: 1660
runtime: 39.640

Filename: src/log.c
Line: 620
Humanstring: "Already up-to-date"
from_version: 1660
runtime: 0.240

{ 1490: {  1490 : 31,
           1500 : 1,
           1510 : 2,
        },
  1500: {  1500: 35,
           1520: 10,
           1540:  4,
        },
}
'''

import re
from collections import defaultdict, OrderedDict


def compute_update_matrix(update_messages):
    from_version_pattern = "^current_version=(\d+)$"
    to_version_pattern = "^server_version=(\d+)$"

    from_version_regex = re.compile(from_version_pattern)
    to_version_regex = re.compile(to_version_pattern)

    updates = defaultdict(dict)
    from_version = None
    to_version = None

    for msg in update_messages:
        lines = msg[0].splitlines()
        # ignore malformed payloads
        if len(lines) < 4:
            continue
        from_match = from_version_regex.match(lines[2])
        to_match = to_version_regex.match(lines[3])
        if from_match and to_match:
            from_version = int(from_match.group(1))
            to_version = int(to_match.group(1))
        else:
            continue

        # don't insert if from == to version, since that is not an update
        if from_version == to_version:
            continue

        from_v = updates[from_version]
        # create version from the to_version if it is not already present
        new_from_v = updates[to_version]
        try:
            from_v[to_version] += 1
        except KeyError:
            from_v[to_version] = 1

    builds = list(updates.keys())
    for from_version, to_dict in list(updates.items()):
        keys = list(to_dict.keys())
        for build in builds:
            if build not in keys:
                to_dict[build] = 0

    sorted_updates = OrderedDict(sorted(updates.items()))
    return sorted_updates


# vi: ts=4 et sw=4 sts=4
