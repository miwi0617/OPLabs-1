"""

This module contains all

"""

from flask import request
from app import db
from models.test_result import TestResult
from util.json_helpers import JSON_SUCCESS, JSON_FAILURE
from util.rest.rest_auth import requires_router_token
from . import rest_blueprint
from models.config import TestConfiguration

@rest_blueprint.route("/router/get_config", methods=['POST'])
@requires_router_token()
def get_config():
    ip = request.remote_addr
    token = request.form['router_token'].strip()

    rec = TestResult.get_result_by_token_ip(token, ip)

    if not rec:
        return JSON_FAILURE()

    rec.state = 'running'
    db.session.commit()
    rec.save()

    config = TestConfiguration()

    return JSON_SUCCESS(
            config=config.get_config()
        )

@rest_blueprint.route("/router/edit", methods=['POST'])
@requires_router_token()
def edit():
    ip = request.remote_addr
    token = request.form['router_token'].strip()

    rec = TestResult.get_result_by_token_ip(token, ip)

    if not rec:
        return JSON_FAILURE(
                reason="Invalid token or IP."
                )

    # Columns allowed to be updated and their types
    columns = TestResult.get_public_columns()

    for col in columns:
        if col in request.form:
            col_type = columns[col]
            datum = col_type(request.form[col])
            setattr(rec, col, datum)
            
    rec.save()
    return JSON_SUCCESS()
