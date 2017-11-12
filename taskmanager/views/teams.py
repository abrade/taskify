# -*- coding: utf-8 -*-

import logging as _logging
import json as _json

import pyramid.view as _view

import taskmanager.views as _views
import taskmanager.models as _models
import taskmanager.models.schemas as _schemas

_log = _logging.getLogger(__name__)

@_view.view_defaults(route_name="all_teams")
class Teams(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(request_method="GET", renderer="json")
    def get_all(self):
        with _views.dbsession(self.request) as session:
            teams = session.query(
                _models.Team
            ).all()
            return {
                "result": _views.RESULT_OK,
                "data": _schemas.Team(many=True).dump(teams).data,
            }

    @_view.view_config(request_method="POST", renderer="json")
    def post_team(self):
        try:
            data = self.request.json
        except _json.decoder.JSONDecodeError as decode_error:
            return {
                "result": _views.RESULT_ERROR,
                "error": decode_error.msg,
                "data": None,
            }
        team_name = data.get("name")
        if team_name is None:
            return {
                "result": _views.RESULT_ERROR,
                "error": "No team name is given",
                "data": None,
            }
        with _views.dbsession(self.request) as session:
            team = _models.Team()
            team.name = team_name
            session.add(team)
            session.commit()
            session.refresh(team)

            return {
                "result": _views.RESULT_OK,
                "data": _schemas.Team().dump(team).data,
            }

@_view.view_defaults(route_name="specific_team", renderer="json")
class Team(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(request_method="GET")
    def get_one(self):
        team_id = self.request.matchdict.get("id")
        with _views.dbsession(self.request) as session:
            team = session.query(
                _models.Team
            ).get(team_id)
            if team is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Team with id {team_id} not found",
                    "data": None,
                }
            return {
                "result": _views.RESULT_OK,
                "data": _schemas.Team().dump(team).data,
            }

    @_view.view_config(request_method=["PUT", "PATCH"])
    def update_team(self):
        team_id = self.request.matchdict.get("id")
        try:
            data = self.request.json
        except _json.decoder.JSONDecodeError as decode_error:
            return {
                "result": _views.RESULT_ERROR,
                "error": decode_error.msg,
                "data": None,
            }
        team_name = data.get("name")
        with _views.dbsession(self.request) as session:
            team = session.query(
                _models.Team
            ).get(team_id)
            if team is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Team with id {team_id} not found",
                    "data": None,
                }
            if team_name:
                team.name = team_name

            session.commit()
            return {
                "result": _views.RESULT_OK,
                "data": _schemas.Team().dump(team).data
            }

    @_view.view_config(request_method="DELETE")
    def delete_team(self):
        team_id = self.request.matchdict.get("id")
        with _views.dbsession(self.request) as session:
            team = session.query(
                _models.Team
            ).get(team_id)
            if team is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Team with id {team_id} not found",
                    "data": None,
                }

            session.delete(team)
            session.commit()
            return {
                "result": _views.RESULT_OK,
                "data": None,
            }

def includeme(config):
    config.add_route("all_teams", "/teams")
    config.add_route("specific_team", "/teams/:id")
