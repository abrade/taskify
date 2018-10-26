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
        include_data = self.request.params.get("include_data")
        additional = {}
        if include_data:
            additional["include_data"] = ("team",)

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
                **_schemas.Script(**additional).dump(scripts, many=True).data
            }

    @_view.view_config(request_method="POST", renderer="json")
    def post_script(self):
        try:
            _log.info(self.request.json)
            data = _schemas.Script().load(self.request.json).data
            _log.info(data)
        except AttributeError:
            data = None

        try:
            if not data:
                data = self.request.json
        except _json.decoder.JSONDecodeError as decode_error:
            return {
                "result": _views.RESULT_ERROR,
                "error": decode_error.msg
            }

        include_data = self.request.params.get("include_data")
        additional = {}
        if include_data:
            additional["include_data"] = ("team",)

        script_name = data.get("name")
        script_cmd = data.get("cmd")
        team_id = data.get("team_id")
        def_opt = data.get("default_options", {})
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
            script = _models.Script(
                script_name,
                script_cmd,
                team_id,
                "ACTIVE",
                default_options=def_opt
            )
            session.add(script)
            session.commit()
            session.refresh(script)

            return {
                "result": _views.RESULT_OK,
                **_schemas.Script(**additional).dump(script).data
            }


@_view.view_defaults(route_name="specific_script")
class Script(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(request_method="GET", renderer="json")
    def get_script(self):
        script_id = self.request.matchdict.get("id")
        include_data = self.request.params.get("include_data")
        additional = {}
        if include_data:
            additional["include_data"] = ("team",)

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
                **_schemas.Script(**additional).dump(script).data,
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
                script.cmd = cmd
            if name:
                script.name = name
            session.commit()
            session.refresh(script)

        return {
            "result": _views.RESULT_OK,
            "data": _schemas.Script().dump(script).data["data"],
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
            "data": _schemas.Script().dump(script).data["data"],
        }


@_view.view_defaults(route_name="script_name")
class ScriptName(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(request_method="GET", renderer="json")
    def get_script(self):
        script_name = self.request.matchdict.get("name")
        include_data = self.request.params.get("include_data")
        additional = {}
        if include_data:
            additional["include_data"] = ("team",)

        with _views.dbsession(self.request) as session:
            script = session.query(
                _models.Script
            ).filter_by(name=script_name).all()
            print(script)
            if script is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Script with id {script_name} not found",
                    "data": None,
                }
            return {
                "result": _views.RESULT_OK,
                **_schemas.Script(**additional).dump(script[0]).data,
            }


def includeme(config):
    config.add_route("all_scripts", "/scripts")
    config.add_route("specific_script", "/scripts/:id")
    config.add_route("script_name", "/scripts/name/:name")
