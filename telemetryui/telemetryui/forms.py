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

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    HiddenField,
    TextField,
    SelectMultipleField)
from wtforms.fields.html5 import DateField
from wtforms.validators import (
    InputRequired,
    Length,
    Regexp,
    Optional)
from wtforms.widgets import (
    html_params,
    HTMLString)


class RecordFilterForm(FlaskForm):
    system_name = SelectField('OS Name',  coerce=str, validators=[InputRequired()])
    build = SelectField('Version', coerce=str, validators=[InputRequired()])
    classification = SelectField('Classification', coerce=str,  validators=[InputRequired()])
    severity = SelectField('Severity',  coerce=str, validators=[InputRequired()])
    machine_id = TextField('Machine ID')
    payload = TextField('Payload REGEX')
    not_payload = TextField('Payload NOT REGEX')
    data_source = SelectField('Source',  coerce=str)
    from_date = DateField('From date', validators=[Optional()])
    to_date = DateField('To date', validators=[Optional()])


class GuiltyDetailsForm(FlaskForm):
    comment = StringField('Comment (80 characters max)', validators=[Length(max=80)])
    guilty_id = HiddenField('Guilty ID (autopopulated)', validators=[Regexp('[0-9]+')])
    hidden = SelectField('Hide this guilty?', choices=[('no', 'no'), ('yes', 'yes')], default='no', validators=[InputRequired()])


class GuiltyAddForm(FlaskForm):
    funcmod = SelectField('Function [Module]', coerce=str, validators=[InputRequired()])


class GuiltyRemoveForm(FlaskForm):
    funcmod = SelectField('Function [Module]', coerce=str, validators=[InputRequired()])


class GuiltyHiddenForm(FlaskForm):
    funcmod = SelectField('Function [Module]', coerce=str, validators=[InputRequired()])


# TODO: eventually the 'confirm' field should be unhidden and populated with
# the results of a prompt for the user's confirmation for carrying out the reset
class GuiltyResetForm(FlaskForm):
    confirm = HiddenField('Confirm reset (autopopulated)', default='yes', validators=[Regexp('yes')])


# Custom widget derived from the example in the docs:
# https://wtforms.readthedocs.io/en/latest/widgets.html
def select_multi_checkbox(field, ul_class='', li_class='', **kwargs):
    kwargs.setdefault('type', 'checkbox')
    field_id = kwargs.pop('id', field.id)
    html = ['<ul {}>\n'.format(html_params(id=field_id, class_=ul_class))]
    for index, (value, label, checked) in enumerate(field.iter_choices()):
        choice_id = '{}{}'.format(field_id, index)
        options = dict(kwargs, name=field.name, value=value, id=choice_id)
        if checked:
            options['checked'] = 'checked'
        html.append('<li {}>\n'.format(html_params(class_=li_class)))
        html.append('<input {} />\n'.format(html_params(**options)))
        html.append('<label for="{}">{}</label>\n</li>\n'.format(field_id, label))
    html.append('</ul>\n')
    return HTMLString(''.join(html))


# For modifying the guilty blacklist according to the backtrace frames selected
class GuiltyEditOneForm(FlaskForm):
    frames = SelectMultipleField(widget=select_multi_checkbox,
                                 render_kw={'ul_class': 'list-group',
                                            'li_class': 'list-group-item'})


# vi: ts=4 et sw=4 sts=4
