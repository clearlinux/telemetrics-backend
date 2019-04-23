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

try:
    from uwsgidecorators import spool
except ImportError:
    def spool(f):
        f.spool = f
        return f

# Alias for uwsgi spool feature. Using this feature to async data processing from
# different probes.
# Aliasing this feature will make it easier in the future to move to a different
# product if scaling becomes a problem.
parser_spooler = spool
