# -*- coding: utf-8 -*-
#
# Copyright 2014 Nicolas Thauvin. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHORS ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, \
     SelectMultipleField
from wtforms import widgets
from wtforms.validators import InputRequired, Email, EqualTo

# Custom fields
class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


# Register Form
class RegisterForm(Form):
    username = StringField(u'Username', [InputRequired()])
    fullname = StringField(u'Full name', [InputRequired()])
    email = StringField(u'E-mail', [InputRequired(), Email()])
    password = PasswordField(u'Password', [InputRequired(),
                                           EqualTo('confirm_password',
                                                   message='Passwords must match')])
    confirm_password = PasswordField(u'Confirm password')
    terms = BooleanField(u'I have read and accept the terms of service', [InputRequired()])

# Login Form
class LoginForm(Form):
    username = StringField(u'Username', [InputRequired()])
    password = PasswordField(u'Password', [InputRequired()])

# Profile Form
class ProfileForm(Form):
    fullname = StringField(u'Full name', [InputRequired()])
    email = StringField(u'E-mail', [InputRequired(), Email()])
    password = PasswordField(u'Password', [InputRequired(),
                                           EqualTo('confirm_password',
                                                   message='Passwords must match')])
    confirm_password = PasswordField(u'Confirm password')

# Form use to save a new query
class AddQueryForm(Form):
    title = StringField(u'Title', [InputRequired()])
    query = TextAreaField(u'Query', [InputRequired()])
    versions = MultiCheckboxField(u'Supported versions', coerce=int)
    description = TextAreaField(u'Description')
    tags = StringField(u'Tags')
