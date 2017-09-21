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

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import cast
from sqlalchemy.sql.expression import desc
from sqlalchemy.sql.expression import case
from sqlalchemy.sql import text
from time import time, localtime, strftime, mktime, strptime, gmtime
from distutils.version import LooseVersion

from . import app

db = SQLAlchemy(app)

MAX_WEEK_KEEP_RECORDS = app.config.get("MAX_WEEK_KEEP_RECORDS", 5)


class Classification(db.Model):
    __tablename__ = 'classification'
    id = db.Column(db.Integer, primary_key=True)
    classification = db.Column(db.String)
    domain = db.Column(db.String)
    probe = db.Column(db.String)

    def __init__(self, class_str):
        self.classification = class_str


class Build(db.Model):
    __tablename__ = 'build'
    id = db.Column(db.Integer, primary_key=True)
    build = db.Column(db.String)

    def __init__(self, build_num):
        self.build = build_num


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
        q = q.filter(Guilty.hide is True)
        q = q.order_by(Guilty.function)
        return q.all()


class Record(db.Model):
    __tablename__ = 'records'
    id = db.Column(db.Integer, primary_key=True)
    severity = db.Column(db.Integer)
    machine = db.Column(db.String, default='')
    machine_id = db.Column(db.String, default='')
    architecture = db.Column(db.String)
    kernel_version = db.Column(db.String, default=0)
    os_name = db.Column(db.String)
    record_format_version = db.Column(db.Integer, default=0)
    payload_format_version = db.Column(db.Integer)
    payload = db.Column(db.LargeBinary)
    tsp = db.Column(db.Integer)
    tsp_server = db.Column(db.Integer)
    buildstamp = db.Column(db.String, default='')
    backtrace = db.Column(db.String, default='')
    guilty = db.Column(db.String, default='')
    dupe_of = db.Column(db.Integer, default=0)
    dupecount = db.Column(db.Integer, default=0)
    dupemaster = db.Column(db.Boolean, default=False)
    security = db.Column(db.Boolean, default=False)
    hide = db.Column(db.Boolean, default=False)
    processed = db.Column(db.Boolean, default=False)
    icon = db.Column(db.String, default='')
    classification_id = db.Column(db.Integer, db.ForeignKey('classification.id'))
    build_id = db.Column(db.Integer, db.ForeignKey('build.id'))
    guilty_id = db.Column(db.Integer, db.ForeignKey('guilty.id'))
    external = db.Column(db.Boolean, default=False)
    board_name = db.Column(db.String, default='')
    bios_version = db.Column(db.String, default='')
    cpu_model = db.Column(db.String, default='')

    classification = db.relationship('Classification', backref=db.backref('records', lazy='dynamic'), lazy='joined')
    build = db.relationship('Build', backref=db.backref('records', lazy='dynamic'), lazy='joined')
    guilty = db.relationship('Guilty', backref=db.backref('records', lazy='dynamic'), lazy='joined')

    def __init__(self, machine_id, host_type, severity, classification, build, architecture, kernel_version,
                 record_format_version, ts_capture, ts_reception, payload_format_version, os_name,
                 board_name, bios_version, cpu_model, external, payload):
        self.machine_id = machine_id
        self.machine = host_type
        self.architecture = architecture
        self.classification = classification
        self.backtrace = payload
        self.build = build
        self.kernel_version = kernel_version
        self.record_format_version = record_format_version
        self.severity = severity
        self.tsp = ts_capture
        self.tsp_server = ts_reception
        self.payload_format_version = payload_format_version
        self.os_name = os_name
        self.external = external
        self.board_name = board_name
        self.bios_version = bios_version
        self.cpu_model = cpu_model

        try:
            self.payload = payload.encode('utf-8')
        except UnicodeError:
            self.payload = payload.encode('latin-1')

    def __repr__(self):
        return "<Record(id='{}', class='{}', build='{}', created='{}')>".format(self.id, self.classification, self.build, strftime("%a, %d %b %Y %H:%M:%S", localtime(self.tsp)))

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self):
        record = {
            'machine_id': self.machine_id,
            'machine_type': self.machine,
            'arch': self.architecture,
            'build': self.build.build,
            'kernel_version': self.kernel_version,
            'ts_capture': strftime('%Y-%m-%d %H:%M:%S UTC', gmtime(self.tsp)),
            'ts_reception': strftime('%Y-%m-%d %H:%M:%S UTC', gmtime(self.tsp_server)),
            'severity': self.severity,
            'classification': self.classification.classification,
            'record_format_version': self.record_format_version,
            'payload': self.backtrace,
            'board_name': self.board_name,
            'bios_version': self.bios_version,
            'cpu_model': self.cpu_model,
        }
        return record

    # for the exported CSV rows
    def to_list(self):
        record = [
            self.id,
            self.external,
            self.tsp_server,
            self.severity,
            self.classification.classification,
            self.build.build,
            self.machine_id,
            self.backtrace
        ]
        return record

    @staticmethod
    def list():
        return Record.query.all()

    @staticmethod
    def create(machine_id, host_type, severity, classification, build, architecture, kernel_version,
               record_format_version, ts_capture, ts_reception, payload_format_version, os_name,
               board_name, bios_version, cpu_model, external, payload):
        try:
            record = Record(machine_id, host_type, severity, classification, build, architecture, kernel_version,
                            record_format_version, ts_capture, ts_reception, payload_format_version, os_name,
                            board_name, bios_version, cpu_model, external, payload)
            db.session.add(record)
            db.session.commit()
            return record
        except:
            db.session.rollback()
            raise

    @staticmethod
    def query_records(build, classification, severity, machine_id, limit, interval_sec=None):
        records = Record.query
        if build is not None:
            records = records.join(Record.build).filter_by(build=build)
        if classification is not None:
            records = records.join(Record.classification).filter_by(classification=classification)
        if severity is not None:
            records = records.filter(Record.severity == severity)
        if machine_id is not None:
            records = records.filter(Record.machine_id == machine_id)

        if interval_sec is not None:
            current_time = time()
            secs_in_past = current_time - interval_sec
            # Due to time skew on client systems, delayed sends due to
            # spooling, etc, tsp_server works better as the reference
            # timestamp.
            records = records.filter(Record.tsp_server > secs_in_past)

        records = records.order_by(Record.id.desc())

        if limit is not None:
            records = records.limit(limit)

        return records.all()

    @staticmethod
    def get_record(record_id):
        record = Record.query.filter_by(id=record_id).first()
        return record

    @staticmethod
    def filter_records(build, classification, severity, machine_id=None, os_name=None, limit=None, from_date=None,
                       to_date=None, payload=None, not_payload=None):
        records = Record.query
        if build is not None:
            records = records.join(Record.build).filter_by(build=build)
        if classification is not None:
            if isinstance(classification, list):
                records = records.join(Record.classification).filter(Classification.classification.in_(classification))
            else:
                records = records.join(Record.classification).filter(Classification.classification.like(classification))
        if severity is not None:
            records = records.filter(Record.severity == severity)
        if os_name is not None:
            records = records.filter(Record.os_name == os_name)
        if machine_id is not None:
            records = records.filter(Record.machine_id == machine_id)
        if from_date is not None:
            from_date = mktime(strptime(from_date, "%Y-%m-%d"))
            records = records.filter(Record.tsp >= from_date)
        if to_date is not None:
            to_date = mktime(strptime(to_date, "%Y-%m-%d"))
            records = records.filter(Record.tsp < to_date)
        if payload is not None:
            records = records.filter(Record.backtrace.op('~')(payload))
        if not_payload is not None:
            records = records.filter(~Record.backtrace.op('~')(not_payload))

        records = records.order_by(Record.id.desc())

        if limit is not None:
            records = records.limit(limit)

        return records

    @staticmethod
    def delete_records():
        try:
            sec_weeks = MAX_WEEK_KEEP_RECORDS * 7 * 24 * 60 * 60
            current_time = time()
            time_weeks_ago = current_time - sec_weeks
            q = db.session.query(Record).filter(Record.tsp_server < time_weeks_ago)
            count = q.delete(synchronize_session=False)
            db.session.commit()
            print("Deleted {} old records".format(count))
        except:
            db.session.rollback()

    @staticmethod
    def get_recordcnts_by_build():
        q = db.session.query(Build.build, db.func.count(Record.id)).join(Record.build)
        q = q.filter(Build.build.op('~')('^[0-9]+$'))
        q = q.group_by(Build.build).order_by(cast(Build.build, db.Integer)).all()
        return q

    @staticmethod
    def get_builds():
        q = db.session.query(Build.build)
        q = q.order_by(Build.build)
        return sorted(q.all(), key=lambda x: LooseVersion(x[0]), reverse=True)

    @staticmethod
    def get_recordcnts_by_classification():
        q = db.session.query(Classification.classification, db.func.count(Record.id))
        q = q.join(Record.classification)
        q = q.group_by(Classification.classification)
        return q.all()

    @staticmethod
    def get_classifications(with_regex=False):
        q = db.session.query(Classification.classification)
        q = q.order_by(Classification.classification)
        if with_regex:
            cs_regex = [cs[0] for cs in q.all()]
            parts = ["{0}/{1}".format(cs.split("/")[0], cs.split("/")[1]) for cs in cs_regex]
            parts.extend([cs.split("/")[0] for cs in parts])
            cs_regex.extend([x + "/*" for x in set([cs for cs in parts if parts.count(cs) > 1])])
            cs_regex.sort()
            return cs_regex
        return q.all()

    @staticmethod
    def get_os_map():
        q = db.session.query(Record.os_name, Build.build).join(Record.build).order_by(Record.os_name).group_by(Record.os_name, Build.build).all()
        result = {}
        for x in q:
            result.setdefault(x[0], []).append(x[1])
        return result

    @staticmethod
    def get_recordcnts_by_machine_type():
        q = db.session.query(Record.machine, db.func.count(Record.id)).group_by(Record.machine).all()
        return q

    @staticmethod
    def get_recordcnts_by_severity():
        q = db.session.query(Record.severity, db.func.count(Record.id)).group_by(Record.severity).all()
        return q

    @staticmethod
    def get_crashcnts_by_class(classes=None):
        q = db.session.query(Classification.classification, db.func.count(Record.id))
        q = q.join(Record)
        if classes:
            q = q.filter(Classification.classification.in_(classes))
        else:
            q = q.filter(Classification.classification.like('org.clearlinux/crash/%'))
        q = q.group_by(Classification.classification)
        return q.all()

    @staticmethod
    def get_crashcnts_by_build(classes=None):
        q = db.session.query(Build.build, db.func.count(Record.id)).join(Record).join(Classification)
        if not classes:
            classes = ['org.clearlinux/crash/clr']
        q = q.filter(Classification.classification.in_(classes))
        q = q.filter(Build.build.op('~')('^[0-9]+$'))
        q = q.group_by(Build.build)
        q = q.order_by(desc(cast(Build.build, db.Integer)))
        q = q.limit(10)
        return q.all()

    @staticmethod
    def get_top_crash_guilties(classes=None):
        q = db.session.query(Guilty.function, Guilty.module, Build.build, db.func.count(Record.id).label('total'), Guilty.id, Guilty.comment)
        q = q.join(Record)
        q = q.join(Build)
        q = q.join(Classification).filter(Record.classification_id == Classification.id)
        if not classes:
            classes = ['org.clearlinux/crash/clr']
        q = q.filter(Classification.classification.in_(classes))
        q = q.filter(Build.build.op('~')('^[0-9][0-9]+$'))
        q = q.filter(Guilty.hide is False)
        q = q.group_by(Guilty.function, Guilty.module, Guilty.comment, Guilty.id, Build.build)
        q = q.order_by(desc(cast(Build.build, db.Integer)), desc('total'))
        # query for records created in the last week (~ 10 Clear builds)
        q = q.filter(Build.build.in_(sorted(tuple(set([x[2] for x in q.all()])), key=lambda x: int(x))[-8:]))
        interval_sec = 24 * 60 * 60 * 7
        current_time = time()
        sec_in_past = current_time - interval_sec
        q = q.filter(Record.tsp > sec_in_past)
        return q.all()

    @staticmethod
    def get_new_crash_records(classes=None, _id=None):
        q = db.session.query(Record).join(Classification)
        if not classes:
            classes = ['org.clearlinux/crash/clr']
        q = q.filter(Classification.classification.in_(classes))
        q = q.filter(Record.os_name == 'clear-linux-os')
        q = q.filter(Record.processed is False)
        if _id:
            q = q.filter(Record.id == _id)
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
        q = db.session.query(Record.backtrace, Record.id).join(Classification)
        # Short circuit if we know the record ID
        if record_id:
            q = q.filter(Record.id == record_id)
            return q.first()
        if build:
            q = q.join(Build)
            q = q.filter(Build.build == build)
        if not classes:
            classes = ['org.clearlinux/crash/clr']
        q = q.filter(Classification.classification.in_(classes))
        q = q.filter(Record.os_name == 'clear-linux-os')
        if guilty_id:
            q = q.filter(Record.guilty_id == guilty_id)
        if machine_id:
            q = q.filter(Record.machine_id == machine_id)
        if most_recent:
            interval_sec = 24 * 60 * 60 * int(most_recent)
            current_time = time()
            sec_in_past = current_time - interval_sec
            q = q.filter(Record.tsp > sec_in_past)
        return q.all()

    @staticmethod
    def reset_processed_records(classes=None, id=None):
        q = db.session.query(Record).join(Classification).join(Build)
        if not classes:
            classes = ['org.clearlinux/crash/clr']
        q = q.filter(Classification.classification.in_(classes))
        q = q.filter(Record.os_name == 'clear-linux-os')
        if id:
            q = q.filter(Record.id == id)
        records = q.all()
        for r in records:
            r.processed = False
        db.session.commit()

    @staticmethod
    def get_machine_ids_for_guilty(id, most_recent=None):
        q = db.session.query(Build.build, Record.machine_id, db.func.count(Record.id).label('total'), Record.guilty_id)
        q = q.join(Record)
        q = q.filter(Record.guilty_id == id)
        q = q.filter(Record.os_name == 'clear-linux-os')
        q = q.filter(Build.build.op('~')('^[0-9][0-9]+$'))
        q = q.group_by(Build.build, Record.machine_id, Record.guilty_id)
        q = q.order_by(desc(cast(Build.build, db.Integer)), desc('total'))
        if most_recent:
            interval_sec = 24 * 60 * 60 * int(most_recent)
            current_time = time()
            sec_in_past = current_time - interval_sec
            q = q.filter(Record.tsp > sec_in_past)
        return q.all()

    @staticmethod
    def get_update_msgs():
        q = db.session.query(Record.backtrace).join(Classification)
        q = q.filter(Classification.classification == "org.clearlinux/swupd-client/update")

        sec_2_weeks = 24 * 60 * 60 * 7
        current_time = time()
        time_2_weeks_ago = current_time - sec_2_weeks

        # query for records created in that last 2 weeks
        q = q.filter(Record.tsp > time_2_weeks_ago)
        return q

    @staticmethod
    def get_swupd_msgs(most_recent=None):
        q = db.session.query(Record.tsp, Record.machine_id, Record.backtrace).join(Classification)
        q = q.filter(Classification.classification.like('org.clearlinux/swupd-client/%'))

        if most_recent:
            interval_sec = 24 * 60 * 60 * int(most_recent)
            current_time = time()
            sec_in_past = current_time - interval_sec
            q = q.filter(Record.tsp > sec_in_past)

        q = q.order_by(desc(Record.tsp))
        return q

    @staticmethod
    def get_heartbeat_msgs(most_recent=None):
        # These two expressions are SQL CASE conditional expressions, later
        # used within count(distinct ...) aggregates for the query.
        internal_expr = case([(Record.external is False, Record.machine_id), ]).label('internal_count')
        external_expr = case([(Record.external is True, Record.machine_id), ]).label('external_count')

        q = db.session.query(Build.build, db.func.count(db.distinct(internal_expr)), db.func.count(db.distinct(external_expr)))
        q = q.join(Record).join(Classification)
        q = q.filter(Classification.classification == "org.clearlinux/heartbeat/ping")
        q = q.filter(Record.os_name == 'clear-linux-os')
        q = q.group_by(Build.build)

        if most_recent:
            interval_sec = 24 * 60 * 60 * int(most_recent)
            current_time = time()
            sec_in_past = current_time - interval_sec
            q = q.filter(Record.tsp > sec_in_past)

        q = q.order_by(cast(Build.build, db.Integer))
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
