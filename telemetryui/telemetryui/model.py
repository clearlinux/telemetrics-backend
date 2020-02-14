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

import itertools
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import cast
from sqlalchemy.sql.expression import desc
from sqlalchemy.sql.expression import case
from time import time, localtime, strftime, mktime, strptime, gmtime
from distutils.version import LooseVersion

from . import app

db = SQLAlchemy(app)


class Guilty(db.Model):
    __tablename__ = 'guilty'
    id = db.Column(db.Integer, primary_key=True)
    function = db.Column(db.String)
    module = db.Column(db.String)
    comment = db.Column(db.String)
    hide = db.Column(db.Boolean, default=False)

    def __init__(self, func, mod):
        self.function = func
        self.module = mod

    @staticmethod
    def update_comment(guilty_id, comment):
        guilty = Guilty.query.filter_by(id=guilty_id).first()
        guilty.comment = comment
        db.session.commit()

    @staticmethod
    def get_function(guilty_id):
        guilty = Guilty.query.filter_by(id=guilty_id).first()
        return guilty and guilty.function or ""

    @staticmethod
    def get_module(guilty_id):
        guilty = Guilty.query.filter_by(id=guilty_id).first()
        return guilty and guilty.module or ""

    @staticmethod
    def update_hidden(guilty_id, status):
        guilty = Guilty.query.filter_by(id=guilty_id).first()
        guilty.hide = status
        db.session.commit()

    @staticmethod
    def get_hidden_value(guilty_id):
        guilty = Guilty.query.filter_by(id=guilty_id).first()
        return guilty and guilty.hide or False

    @staticmethod
    def get_hidden_guilties():
        q = db.session.query(Guilty.id, Guilty.function, Guilty.module)
        q = q.filter(Guilty.hide == True)
        q = q.order_by(Guilty.function)
        return q.all()


class Record(db.Model):
    __tablename__ = 'records'
    id = db.Column(db.Integer, primary_key=True)
    architecture = db.Column(db.Text)
    bios_version = db.Column(db.Text, default='')
    board_name = db.Column(db.Text, default='')
    build = db.Column(db.Text, nullable=False)
    classification = db.Column(db.Text, nullable=False)
    cpu_model = db.Column(db.Text, default='')
    event_id = db.Column(db.Text, default='')
    external = db.Column(db.Boolean, default=False)
    host_type = db.Column(db.Text, default='')
    kernel_version = db.Column(db.Text, default=0)
    machine_id = db.Column(db.Text, default='')
    payload_version = db.Column(db.Integer)
    record_version = db.Column(db.Integer, default=0)
    severity = db.Column(db.Integer)
    system_name = db.Column(db.Text)
    timestamp_client = db.Column(db.Numeric)
    timestamp_server = db.Column(db.Numeric, nullable=False)
    payload = db.Column(db.Text, nullable=False)

    processed = db.Column(db.Boolean, default=False)
    guilty_id = db.Column(db.Integer, db.ForeignKey('guilty.id'))

    guilty = db.Column(db.Text, default='')
    guilty = db.relationship('Guilty', backref=db.backref('records', lazy='dynamic'), lazy='joined')

    def __init__(self, machine_id, host_type, severity, classification, build, architecture, kernel_version,
                 record_version, ts_capture, ts_reception, payload_version, system_name,
                 board_name, bios_version, cpu_model, event_id, external, payload):
        self.machine_id = machine_id
        self.host_type = host_type
        self.architecture = architecture
        self.classification = classification
        self.build = build
        self.kernel_version = kernel_version
        self.record_version = record_version
        self.severity = severity
        self.timestamp_client = ts_capture
        self.timestamp_server = ts_reception
        self.payload_version = payload_version
        self.system_name = system_name
        self.external = external
        self.board_name = board_name
        self.bios_version = bios_version
        self.cpu_model = cpu_model
        self.event_id = event_id
        self.payload = payload


    def __repr__(self):
        return "<Record(id='{}', class='{}', build='{}', created='{}')>".format(self.id, self.classification, self.build, strftime("%a, %d %b %Y %H:%M:%S", localtime(self.timestamp_client)))

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self):
        record = {
            'id': self.id,
            'machine_id': self.machine_id,
            'machine_type': self.host_type,
            'arch': self.architecture,
            'build': self.build,
            'kernel_version': self.kernel_version,
            'ts_capture': strftime('%Y-%m-%d %H:%M:%S UTC', gmtime(self.timestamp_client)),
            'ts_reception': strftime('%Y-%m-%d %H:%M:%S UTC', gmtime(self.timestamp_server)),
            'severity': self.severity,
            'classification': self.classification,
            'record_version': self.record_version,
            'payload': self.payload,
            'board_name': self.board_name,
            'bios_version': self.bios_version,
            'cpu_model': self.cpu_model,
            'event_id': self.event_id,
            'external': self.external,
        }
        return record

    # for the exported CSV rows
    def to_list(self):
        record = [
            self.id,
            self.external,
            self.timestamp_server,
            self.severity,
            self.classification,
            self.build,
            self.machine_id,
            self.payload
        ]
        return record

    @staticmethod
    def list():
        return Record.query.all()

    @staticmethod
    def create(machine_id, host_type, severity, classification, build, architecture, kernel_version,
               record_version, ts_capture, ts_reception, payload_version, system_name,
               board_name, bios_version, cpu_model, event_id, external, payload):
        try:
            record = Record(machine_id, host_type, severity, classification, build, architecture, kernel_version,
                            record_version, ts_capture, ts_reception, payload_version, system_name,
                            board_name, bios_version, cpu_model, event_id, external, payload)
            db.session.add(record)
            db.session.commit()
            return record
        except:
            db.session.rollback()
            raise

    @staticmethod
    def query_records(build, classification, severity, machine_id, limit,
                      interval_sec=None, ts_capture=None, from_id=None):
        records = Record.query
        if build is not None:
            records = records.filter_by(build=build)
        if classification is not None:
            records = records.filter_by(classification=classification)
        if severity is not None:
            records = records.filter(Record.severity == severity)
        if machine_id is not None:
            records = records.filter(Record.machine_id == machine_id)
        if from_id is not None:
            records = records.filter(Record.id >= from_id)
        if ts_capture is not None:
            records = records.filter(Record.timestamp_client > ts_capture)

        if interval_sec is not None:
            current_time = time()
            secs_in_past = current_time - interval_sec
            # Due to time skew on client systems, delayed sends due to
            # spooling, etc, timestamp_server works better as the reference
            # timestamp.
            records = records.filter(Record.timestamp_server > secs_in_past)

        records = records.order_by(Record.id.desc())

        if limit is not None:
            records = records.limit(limit)

        return records.all()

    @staticmethod
    def get_record(record_id):
        record = Record.query.filter_by(id=record_id).first()
        return record

    @staticmethod
    def filter_records(build, classification, severity, machine_id=None, system_name=None, limit=None, from_date=None,
                       to_date=None, payload=None, not_payload=None, data_source=None):
        records = Record.query
        if build is not None:
            records = records.filter_by(build=build)
        if classification is not None:
            if isinstance(classification, list):
                records = records.filter(Record.classification.in_(classification))
            else:
                records = records.filter(Record.classification.like(classification))
        if severity is not None:
            records = records.filter(Record.severity == severity)
        if system_name is not None:
            records = records.filter(Record.system_name == system_name)
        if machine_id is not None:
            records = records.filter(Record.machine_id == machine_id)
        if from_date is not None:
            from_date = mktime(strptime(from_date, "%Y-%m-%d"))
            records = records.filter(Record.timestamp_client >= from_date)
        if to_date is not None:
            to_date = mktime(strptime(to_date, "%Y-%m-%d"))
            records = records.filter(Record.timestamp_client < to_date)
        if payload is not None:
            records = records.filter(Record.payload.op('~')(payload))
        if not_payload is not None:
            records = records.filter(~Record.payload.op('~')(not_payload))
        if data_source is not None:
            if data_source == "external":
                records = records.filter(Record.external == True)
            elif data_source == "internal":
                records = records.filter(Record.external == False)

        records = records.order_by(Record.id.desc())

        if limit is not None:
            records = records.limit(limit)

        return records

    @staticmethod
    def delete_records():
        MAX_DAYS_KEEP_UNFILTERED_RECORDS = app.config.get("MAX_DAYS_KEEP_UNFILTERED_RECORDS", 35)
        PURGE_FILTERED_RECORDS = app.config.get("PURGE_FILTERED_RECORDS", {})
        try:
            def purge_field(field):
                for name in PURGE_FILTERED_RECORDS[field].keys():
                    if PURGE_FILTERED_RECORDS[field][name]:
                        age = time() - PURGE_FILTERED_RECORDS[field][name] * 24 * 60 * 60
                        q = db.session.query(Record)
                        if field == 'classification':
                            q = q.filter(Record.classification.like(name.replace("*", "%")))
                        else:
                            q = q.filter(getattr(Record, field) == name)
                        q = q.filter(Record.timestamp_server < age)
                        if q.all():
                            count = db.session.query(Record).filter(Record.id.in_([x.id for x in q.all()])).delete(synchronize_session=False)
                            print("Deleted {} {} records".format(count, name))
            for field in PURGE_FILTERED_RECORDS.keys():
                purge_field(field)
            if MAX_DAYS_KEEP_UNFILTERED_RECORDS:
                unfiltered_age = time() - MAX_DAYS_KEEP_UNFILTERED_RECORDS * 24 * 60 * 60
                q = db.session.query(Record.id)
                for field in PURGE_FILTERED_RECORDS.keys():
                    if field == 'classification':
                        for classification in PURGE_FILTERED_RECORDS[field].keys():
                            q = q.filter(~Record.classification.like(classification.replace("*", "%")))
                    else:
                        for name in PURGE_FILTERED_RECORDS[field].keys():
                            q = q.filter(getattr(Record, field) != name)
                q = q.filter(Record.timestamp_server < unfiltered_age)
                if q.all():
                    count = db.session.query(Record).filter(Record.id.in_([x.id for x in q.all()])).delete(synchronize_session=False)
                    print("Deleted {} old records".format(count))
            db.session.commit()
        except Exception as e:
            app.logger.error("Record purging failed")
            app.logger.error(e)
            db.session.rollback()

    @staticmethod
    def get_recordcnts_by_build():
        q = db.session.query(Record.build, db.func.count(Record.id))
        q = q.filter(Record.build.op('~')('^[0-9]+$'))
        q = q.group_by(Record.build).order_by(cast(Record.build, db.Integer)).all()
        return q

    @staticmethod
    def get_builds():
        q = db.session.query(Record.build).distinct()
        q = q.filter(Record.build.op('~')('^[0-9]+$'))
        q = q.order_by(Record.build)
        return sorted(q.all(), key=lambda x: LooseVersion(x[0]), reverse=True)

    @staticmethod
    def get_recordcnts_by_classification():
        q = db.session.query(Record.classification, db.func.count(Record.id).label('total'))
        q = q.group_by(Record.classification)
        q = q.order_by(desc('total'))
        return q.all()

    @staticmethod
    def expand_class(D):
        A, B, C = D
        return ["{}/*".format(A), "{}/{}/*".format(A, B), "{}/{}/{}".format(A, B, C)]

    @staticmethod
    def get_classifications(with_regex=False):
        q = db.session.query(Record.classification).distinct()
        if with_regex:
            classes = [Record.expand_class(c[0].split('/')) for c in q.all()]
            return sorted(set(itertools.chain(*classes)))
        else:
            return q.all()

    @staticmethod
    def get_os_map():
        q = db.session.query(Record.system_name, Record.build).order_by(Record.system_name).group_by(Record.system_name, Record.build).all()
        result = {}
        for x in q:
            result.setdefault(x[0], []).append(x[1])
        return result

    @staticmethod
    def get_recordcnts_by_machine_type():
        q = db.session.query(Record.host_type, db.func.count(Record.id).label('total'))
        q = q.group_by(Record.host_type)
        q = q.order_by(desc('total'))
        return q.all()

    @staticmethod
    def get_recordcnts_by_severity():
        q = db.session.query(Record.severity, db.func.count(Record.id)).group_by(Record.severity).all()
        return q

    @staticmethod
    def get_crashcnts_by_class(classes=None):
        q = db.session.query(Record.classification, db.func.count(Record.id))
        if classes:
            q = q.filter(Record.classification.in_(classes))
        else:
            q = q.filter(Record.classification.like('org.clearlinux/crash/%'))
        q = q.group_by(Record.classification)
        return q.all()

    @staticmethod
    def get_crashcnts_by_build(classes=None):
        q = db.session.query(Record.build, db.func.count(Record.id))
        if not classes:
            classes = ['org.clearlinux/crash/clr']
        q = q.filter(Record.classification.in_(classes))
        q = q.filter(Record.build.op('~')('^[0-9]+$'))
        q = q.group_by(Record.build)
        q = q.order_by(desc(cast(Record.build, db.Integer)))
        q = q.limit(10)
        return q.all()

    @staticmethod
    def get_top_crash_guilties(classes=None):
        q = db.session.query(Guilty.function, Guilty.module, Record.build, db.func.count(Record.id).label('total'), Guilty.id, Guilty.comment)
        q = q.join(Record)
        if not classes:
            classes = ['org.clearlinux/crash/clr']
        q = q.filter(Record.classification.in_(classes))
        q = q.filter(Record.build.op('~')('^[0-9][0-9]+$'))
        q = q.filter(cast(Record.build, db.Integer) <= 100000)
        q = q.filter(Guilty.hide == False)
        q = q.group_by(Guilty.function, Guilty.module, Guilty.comment, Guilty.id, Record.build)
        q = q.order_by(desc(cast(Record.build, db.Integer)), desc('total'))
        # query for records created in the last week (~ 10 Clear builds)
        q = q.filter(Record.build.in_(sorted(tuple(set([x[2] for x in q.all()])), key=lambda x: int(x))[-8:]))
        interval_sec = 24 * 60 * 60 * 7
        current_time = time()
        sec_in_past = current_time - interval_sec
        q = q.filter(Record.timestamp_client > sec_in_past)
        return q.all()

    @staticmethod
    def get_new_crash_records(classes=None, id=None):
        q = db.session.query(Record)
        if not classes:
            classes = ['org.clearlinux/crash/clr']
        q = q.filter(Record.classification.in_(classes))
        q = q.filter(Record.system_name == 'clear-linux-os')
        q = q.filter(Record.processed == False)
        if id:
            q = q.filter(Record.id == id)
        return q.all()

    @staticmethod
    def set_processed_flag(record):
        record.processed = True

    @staticmethod
    def get_guilty_for_funcmod(func, mod):
        q = db.session.query(Guilty).filter_by(function=func, module=mod).first()
        return q

    @staticmethod
    def get_guilty_id_for_record(record_id):
        q = db.session.query(Guilty.id).join(Record)
        q = q.filter(Record.id == record_id)
        return q.first()

    @staticmethod
    def init_guilty(func, mod):
        return Guilty(func, mod)

    @staticmethod
    def create_guilty_for_record(record, guilty):
        record.guilty = guilty

    @staticmethod
    def commit_guilty_changes():
        # just commit for now
        db.session.commit()

    @staticmethod
    def get_crash_backtraces(classes=None, guilty_id=None, machine_id=None, build=None, most_recent=None, record_id=None):
        q = db.session.query(Record.payload, Record.id)
        # Short circuit if we know the record ID
        if record_id:
            q = q.filter(Record.id == record_id)
            return q.first()
        if build:
            q = q.filter(Record.build == build)
        if not classes:
            classes = ['org.clearlinux/crash/clr']
        q = q.filter(Record.classification.in_(classes))
        q = q.filter(Record.system_name == 'clear-linux-os')
        if guilty_id:
            q = q.filter(Record.guilty_id == guilty_id)
        if machine_id:
            q = q.filter(Record.machine_id == machine_id)
        if most_recent:
            interval_sec = 24 * 60 * 60 * int(most_recent)
            current_time = time()
            sec_in_past = current_time - interval_sec
            q = q.filter(Record.timestamp_client > sec_in_past)
        return q.all()

    @staticmethod
    def reset_processed_records(classes=None, id=None):
        q = db.session.query(Record)
        if not classes:
            classes = ['org.clearlinux/crash/clr']
        q = q.filter(Record.classification.in_(classes))
        q = q.filter(Record.system_name == 'clear-linux-os')
        if id:
            q = q.filter(Record.id == id)
        records = q.all()
        for r in records:
            r.processed = False
        db.session.commit()

    @staticmethod
    def get_machine_ids_for_guilty(id, most_recent=None):
        q = db.session.query(Record.build, Record.machine_id, db.func.count(Record.id).label('total'), Record.guilty_id)
        q = q.filter(Record.guilty_id == id)
        q = q.filter(Record.system_name == 'clear-linux-os')
        q = q.filter(Record.build.op('~')('^[0-9][0-9]+$'))
        q = q.group_by(Record.build, Record.machine_id, Record.guilty_id)
        q = q.order_by(desc(cast(Record.build, db.Integer)), desc('total'))
        if most_recent:
            interval_sec = 24 * 60 * 60 * int(most_recent)
            current_time = time()
            sec_in_past = current_time - interval_sec
            q = q.filter(Record.timestamp_client > sec_in_past)
        return q.all()

    @staticmethod
    def get_update_msgs():
        q = db.session.query(Record.payload)
        q = q.filter(Record.classification == "org.clearlinux/swupd-client/update")

        sec_2_weeks = 24 * 60 * 60 * 7
        current_time = time()
        time_2_weeks_ago = current_time - sec_2_weeks

        # query for records created in that last 2 weeks
        q = q.filter(Record.timestamp_client > time_2_weeks_ago)
        return q.all()

    @staticmethod
    def get_swupd_msgs(most_recent=None):
        q = db.session.query(Record.timestamp_client, Record.machine_id, Record.payload)
        q = q.filter(Record.classification.like('org.clearlinux/swupd-client/%'))

        if most_recent:
            interval_sec = 24 * 60 * 60 * int(most_recent)
            current_time = time()
            sec_in_past = current_time - interval_sec
            q = q.filter(Record.timestamp_client > sec_in_past)

        q = q.order_by(desc(Record.timestamp_client))
        return q

    @staticmethod
    def get_heartbeat_msgs(most_recent=None):
        # These two expressions are SQL CASE conditional expressions, later
        # used within count(distinct ...) aggregates for the query.
        internal_expr = case([(Record.external == False, Record.machine_id), ]).label('internal_count')
        external_expr = case([(Record.external == True, Record.machine_id), ]).label('external_count')

        q = db.session.query(Record.build, db.func.count(db.distinct(internal_expr)), db.func.count(db.distinct(external_expr)))
        q = q.filter(Record.classification == "org.clearlinux/heartbeat/ping")
        q = q.filter(Record.system_name == 'clear-linux-os')
        q = q.group_by(Record.build)

        if most_recent:
            interval_sec = 24 * 60 * 60 * int(most_recent)
            current_time = time()
            sec_in_past = current_time - interval_sec
            q = q.filter(Record.timestamp_client > sec_in_past)

        q = q.order_by(cast(Record.build, db.Integer))
        return q.all()


class GuiltyBlacklist(db.Model):
    __tablename__ = 'guilty_blacklisted'
    id = db.Column(db.Integer, primary_key=True)
    function = db.Column(db.String)
    module = db.Column(db.String)

    def __init__(self, func, mod):
        self.function = func
        self.module = mod

    def __repr__(self):
        return "<GuiltyBlacklist(id='{}', guilty='{}:{}')>".format(self.id, self.function, self.module)

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self):
        guilty = {
            'function': self.function,
            'module': self.module
        }
        return guilty

    @staticmethod
    def add(func, mod):
        try:
            g = GuiltyBlacklist(func, mod)
            db.session.add(g)
            db.session.commit()
            return g
        except:
            db.session.rollback()
            raise

    @staticmethod
    def remove(func, mod):
        q = db.session.query(GuiltyBlacklist)
        q = q.filter_by(function=func, module=mod)
        entry = q.first()
        db.session.delete(entry)
        db.session.commit()

    @staticmethod
    def get_guilties():
        q = db.session.query(GuiltyBlacklist.function, GuiltyBlacklist.module)
        q = q.order_by(GuiltyBlacklist.function)
        return q.all()

    @staticmethod
    def exists(func, mod):
        q = db.session.query(GuiltyBlacklist.function, GuiltyBlacklist.module)
        q = q.filter_by(function=func, module=mod)
        return len(q.all()) != 0 and True or False

    @staticmethod
    def update(to_add, to_remove):
        try:
            for i in to_add:
                if not GuiltyBlacklist.exists(i[0], i[1]):
                    g = GuiltyBlacklist(i[0], i[1])
                    db.session.add(g)
            for i in to_remove:
                if GuiltyBlacklist.exists(i[0], i[1]):
                    q = db.session.query(GuiltyBlacklist)
                    q = q.filter_by(function=i[0], module=i[1])
                    entry = q.first()
                    db.session.delete(entry)
            db.session.commit()
        except:
            db.session.rollback()
            raise

# vi: ts=4 et sw=4 sts=4
