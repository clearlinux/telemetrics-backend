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

from collector.models import db

class Message(db.Model):
    __tablename__ = 'demo_message'
    record_id = db.Column(db.Integer, db.ForeignKey('records.id'))
    payload = buildstamp = db.Column(db.String, default='')

    def __init__(self, **kwargs):
        self.record_id = kwargs.get('record_id', None)
        self.payload = kwargs.get('payload', None)
