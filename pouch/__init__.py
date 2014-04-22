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

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from jinja2_highlight import HighlightExtension
from werkzeug.datastructures import MultiDict

import os, hashlib, psycopg2, re, sqlparse

# app is needed for the following imports
app = Flask(__name__)

from pouch.database import get_db, fetch_from_db, fetch_one_from_db
from pouch.forms import *
from pouch.user import login_required

# Load the code highlight with pygments extension of jinja2
app.jinja_env.add_extension(HighlightExtension)

# Configuration. It is looked up in the following order: hardcoded, in
# the settings.py file at the root of the application, in the path
# exported by the POUCH_SETTINGS environment varable. A place
# overwrites the previous.
app.config.from_object(__name__)

# Hardcoded defaults
app.config.update(dict(
    DSN="dbname=pouch",
    DEBUG=False,
    SECRET_KEY='one hard to find development key',
))

# Load app_root/settings.py
app.config.from_pyfile(os.path.join(app.root_path, 'settings.py'), silent=True)

# Load the file pointed by our envvar
app.config.from_envvar('POUCH_SETTINGS', silent=True)


# Views
@app.route('/')
def index():
    rows = fetch_from_db("""SELECT q.id, q.query, string_agg(distinct v.version, ', ') as versions, q.title, q.description,
      array_agg(distinct t.tag) as tags
    FROM queries q
      LEFT JOIN queries_versions qv ON (q.id = qv.query_id)
      LEFT JOIN versions v on (qv.version_num = v.version_num)
      LEFT JOIN queries_tags qt ON (q.id = qt.query_id)
      LEFT JOIN tags t ON (qt.tag_id = t.id)
    GROUP BY q.id, q.title, q.description
    ORDER BY q.id DESC 
    LIMIT 10""")

    queries = []
    for row in rows:
        queries.append({'id': row['id'],
                        'query': sqlparse.format(row['query'], reindent=True, keyword_case='upper'),
                        'versions': row['versions'],
                        'title': row['title'],
                        'description': row['description'],
                        'tags': row['tags']})
    
    return render_template('index.html', queries=queries)

@app.route('/tag')
def tag_cloud():
    abort(404)

@app.route('/tag/<tag>')
def by_tag(tag):
    abort(404)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = AddQueryForm()

    # Get all the versions
    rows = fetch_from_db("SELECT version_num, version FROM versions ORDER BY 1")
    form.versions.choices = [ (x['version_num'], x['version']) for x in rows ]
    
    if form.validate_on_submit():
        db = get_db()
        try:
            row = fetch_one_from_db("""INSERT INTO queries (query, title, description, account_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id""", (form.query.data, form.title.data, form.description.data, session['user']['id']))
        except psycopg2.DatabaseError:
            flash("An error occured while saving the query")
            db.rollback()
            return render_template("add.html", form=form, page="Save a useful query")

        query_id = row['id']

        # Links to the versions
        # When versions is empty, it means the query works with any versions
        if form.versions.data:
            tuples = [ (query_id, v) for v in form.versions.data ]
            cur = db.cursor()
            try:
                cur.executemany("""INSERT INTO queries_versions (query_id, version_num)
                VALUES (%s, %s)""", tuples)
            except psycopg2.DatabaseError:
                flash("An error occured while saving the query")
                db.rollback()
                return render_template("add.html", form=form, page="Save a useful query")
            
            cur.close()

        # Links to the tags
        try:
            cur = db.cursor()
            for tag in re.split(r'[\s,;]+', form.tags.data):
                # Find or save the tag
                row = fetch_one_from_db("SELECT id FROM tags WHERE tag = lower(%s)", (tag,))
                if not row:
                    row = fetch_one_from_db("INSERT INTO tags (tag) VALUES (lower(%s)) RETURNING id", (tag,))

                cur.execute("INSERT INTO queries_tags (query_id, tag_id) VALUES (%s, %s)", (query_id, row['id']))
            cur.close()
        except psycopg2.DatabaseError:
            flash("An error occured while saving the query")
            db.rollback()
            return render_template("add.html", form=form, page="Save a useful query")

        return redirect(url_for('index'))


    return render_template("add.html", form=form, page="Save a useful query")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if the username is already in the db
        checked = fetch_from_db("select 1 from accounts where account = %s", (form.username.data,))
        if checked:
            # Inject the error message in the form
            form.username.errors = [u'This username is already registered.']
        else:
            row = fetch_one_from_db("""INSERT INTO accounts (account, fullname, password, email)
            VALUES (%s, %s, %s, %s)
            RETURNING id""",
                              (form.username.data, form.fullname.data,
                               hashlib.sha256(form.password.data).hexdigest(),
                               form.email.data))

            # setup session to log the user in directly.
            # show the profile page with the agent key
            session['user'] = { "id": row['id'],
                                "username": form.username.data,
                                "fullname": form.fullname.data,
                                "admin": False }
            
            return redirect(url_for('profile'))

    return render_template("simple_form.html", form=form, page="register")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        row = fetch_one_from_db("""SELECT id, account, fullname, email, is_admin
        FROM accounts
        WHERE account = %s AND password = %s""",
                                (form.username.data,
                                 hashlib.sha256(form.password.data).hexdigest()))
        if row:
            session['user'] = { "id": row['id'], "username": row['account'], 'email': row['email'],
                                "fullname": row['fullname'], "admin": row['is_admin'] }
            
            return redirect(url_for('profile'))

    return render_template("simple_form.html", form=form, page_title="Log In", page="login", button="Log In")


@app.route('/logout')
def logout():
    if 'user' in session:
        del session['user']
        flash("You are logged out.")
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(MultiDict([('fullname', session['user']['fullname']), ('email',session['user']['email'])]))
    if form.validate_on_submit():
        pass
    return render_template("simple_form.html", form=form, page_title="Profile", page="profile", button="Update")

