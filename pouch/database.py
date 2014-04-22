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

from flask import g
from pouch import app
import psycopg2, psycopg2.extras
from psycopg2.extensions import TRANSACTION_STATUS_INTRANS, \
     TRANSACTION_STATUS_INERROR

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'dbconn'):
        g.dbconn = psycopg2.connect(app.config['DSN'])
    return g.dbconn

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'dbconn'):
        if g.dbconn is not None:
            # Commit pending changes
            if g.dbconn.get_transaction_status() == TRANSACTION_STATUS_INTRANS:
                g.dbconn.commit()
            # Do a clean rollback when we have a failed xact
            if g.dbconn.get_transaction_status() == TRANSACTION_STATUS_INERROR:
                g.dbconn.rollback()
            
            g.dbconn.close()

def fetch_from_db(query, params=None):
    """Get all the records from a query."""
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if params is not None:
        cur.execute(query, params)
    else:
        cur.execute(query)
    results = cur.fetchall()
    cur.close()
    return results

def fetch_one_from_db(query, params=None):
    """Get the first record from a query."""
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if params is not None:
        cur.execute(query, params)
    else:
        cur.execute(query)
    result = cur.fetchone()
    cur.close()
    return result
