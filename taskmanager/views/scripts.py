# -*- coding: utf-8 -*-

import logging as _logging
import json as _json

import pyramid.view as _view

import taskmanager.views as _views
import taskmanager.models as _models
import taskmanager.models.schemas as _schemas

_log = _logging.getLogger(__name__)

@_view.view_defaults(route_name="all_scripts")
class Scripts(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(request_method="GET", renderer="json")
    def get_all(self):
        team_id = self.request.params.get("team")
        with _views.dbsession(self.request) as session:
            scripts = session.query(
                _models.Script
            )
            if team_id:
                scripts = scripts.filter(
                    _models.Script.team_id == team_id
                )
            scripts = scripts.all()
            return {
                "result": _views.RESULT_OK,
                "data": _schemas.Script(many=True).dump(scripts).data,
            }

    @_view.view_config(request_method="POST", renderer="json")
    def post_script(self):
        try:
            data = self.request.json
        except _json.decoder.JSONDecodeError as decode_error:
            return {
                "result": _views.RESULT_ERROR,
                "error": decode_error.msg
            }
        script_name = data.get("name")
        script_cmd = data.get("cmd")
        team_id = data.get("team_id")
        if script_name is None:
            return {
                "result": _views.RESULT_ERROR,
                "error": "No script name is given",
                "data": None
            }
        if script_cmd is None:
            return {
                "result": _views.RESULT_ERROR,
                "error": "No script command is given",
                "data": None
            }
        if team_id is None:
            return {
                "result": _views.RESULT_ERROR,
                "error": "No team id is given",
                "data": None
            }
        with _views.dbsession(self.request) as session:
            script = _models.Script()
            script.name = script_name
            script.script = script_cmd
            script.team_id = team_id
            session.add(script)
            session.commit()
            session.refresh(script)

            return {
                "result": _views.RESULT_OK,
                "data": _schemas.Script().dump(script).data
            }

@_view.view_defaults(route_name="specific_script")
class Script(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(request_method="GET", renderer="json")
    def get_script(self):
        script_id = self.request.matchdict.get("id")
        with _views.dbsession(self.request) as session:
            script = session.query(
                _models.Script
            ).get(script_id)
            if script is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Script with id {script_id} not found",
                    "data": None,
                }
            return {
                "result": _views.RESULT_OK,
                "data": _schemas.Script().dump(script).data
            }

    @_view.view_config(request_method="PATCH", renderer="json")
    def update_script(self):
        script_id = self.request.matchdict.get("id")
        try:
            data = self.request.json
        except _json.decoder.JSONDecodeError as decode_error:
            return {
                "result": _views.RESULT_ERROR,
                "error": decode_error.msg
            }
        team_id = data.get("team_id")
        status = data.get("status")
        cmd = data.get("script")
        name = data.get("name")
        with _views.dbsession(self.request) as session:
            script = session.query(
                _models.Script
            ).get(script_id)
            if script is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Script with id {script_id} not found",
                    "data": None,
                }
            if team_id:
                script.team_id = team_id
            if status:
                script.status = status
            if cmd:
                script.script = cmd
            if name:
                script.name = name
            session.commit()
            session.refresh(script)
        return {
            "result": _views.RESULT_OK,
            "data": _schemas.Script().dump(script).data
        }

    @_view.view_config(request_method="DELETE", renderer="json")
    def archive_script(self):
        script_id = self.request.matchdict.get("id")
        with _views.dbsession(self.request) as session:
            script = session.query(
                _models.Script
            ).get(script_id)
            if script is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Script with id {script_id} not found",
                    "data": None,
                }
            script.status = "ARCHIVED"
            session.commit()

        return {
            "result": _views.RESULT_OK,
            "data": _schemas.Script().dump(script).data
        }

def includeme(config):
    config.add_route("all_scripts", "/scripts")
    config.add_route("specific_script", "/scripts/:id")
