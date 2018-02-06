#
# Copyright 2018 Intel Corporation
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


import time
from collector.lib.parser import parser_spooler

CLASSIFICATIONS = ['org.clearlinux/telemetry/b64payload']


@parser_spooler
def parse_payload(**kwargs):
    """
    :param kwargs: classification=<value>,
                   record_id=<value>,
                   payload=<value>
    :return: None
    """
    print("Processing data")
    print(kwargs)
    time.sleep(1)
    print("Data processed")
