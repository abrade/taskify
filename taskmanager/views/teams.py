# -*- coding: utf-8 -*-

import logging as _logging

import taskmanager.views as _views
import taskmanager.models as _models
import taskmanager.models.schemas as _schemas

_log = _logging.getLogger(__name__)


class Teams(_views.BaseResource):
    NAME = "teams"

    @_views.get_all()
    @_views.with_model(output_model=_schemas.Team)
    @_views.with_links
    def get_all(self, page=0, max_entries=20):
        with _views.dbsession(self.request) as session:
            teams = session.query(
                _models.Team
            )
            max_elements = teams.count()
            teams = teams.offset(
                page*max_entries
            ).limit(
                max_entries
            ).all()
            return {
                'meta': {
                    'page': page,
                    'max_entries': max_entries,
                    'max_elements': max_elements,
                },
                'data': teams,
            }

    @_views.post_one()
    @_views.with_model(model=_schemas.Team)
    def post_team(self, post_data):
        team_name = post_data.get("name")
        if team_name is None:
            raise _views.RestAPIException(
                "Not team name is given",
                _views.RESULT_ERROR,
            )
        with _views.dbsession(self.request) as session:
            team = _models.Team(team_name)
            session.add(team)
            session.commit()
            session.refresh(team)

            return team

    @_views.get_one(param='team_id')
    @_views.with_model(output_model=_schemas.Team)
    def get_one(self, team_id):
        with _views.dbsession(self.request) as session:
            team = session.query(
                _models.Team
            ).get(team_id)
            if team is None:
                raise _views.RestAPIException(
                    f"Team with id {team_id} not found",
                    _views.RESULT_NOTFOUND
                )
            return team

    @_views.patch_one(param="team_id")
    @_views.with_model(model=_schemas.Team)
    def update_team(self, team_id, post_data):
        team_name = post_data.get("name")
        with _views.dbsession(self.request) as session:
            team = session.query(
                _models.Team
            ).get(team_id)
            if team is None:
                raise _views.RestAPIException(
                    f"Team with id {team_id} not found",
                    _views.RESULT_NOTFOUND
                )
            if team_name:
                team.name = team_name

            session.commit()
            return team

    @_views.delete_one(param="team_id")
    @_views.with_model(output_model=_schemas.Team)
    def delete_team(self, team_id):
        with _views.dbsession(self.request) as session:
            team = session.query(
                _models.Team
            ).get(team_id)
            if team is None:
                raise _views.RestAPIException(
                    f"Team with id {team_id} not found",
                    _views.RESULT_NOTFOUND,
                )

            session.delete(team)
            session.commit()
            return team


class TeamName(_views.BaseResource):
    NAME = "teams/name"

    @_views.get_one(param="name")
    def get_one(self, name):
        team_name = name
        with _views.dbsession(self.request) as session:
            team = session.query(
                _models.Team
            ).filter_by(name=team_name).all()
            if team is None:
                raise _views.RestAPIException(
                    f"Team with id {team_name} not found",
                    _views.RESULT_NOTFOUND,
                )
            return team[0]


def includeme(config):
    Teams.init_handler(config)
    TeamName.init_handler(config)
