# -*- coding: utf-8 -*-

import logging as _logging

import sqlalchemy.orm as _sa

import taskmanager.views as _views
import taskmanager.models as _models
import taskmanager.models.schemas as _schemas

_log = _logging.getLogger(__name__)


class Scripts(_views.BaseResource):
    NAME = "scripts"

    @_views.get_all()
    @_views.with_model(output_model=_schemas.Script, include=("team",))
    @_views.with_links
    def get_all(self, team_id=None, include_data=None, page=0, size=20):
        with _views.dbsession(self.request) as session:
            scripts = session.query(
                _models.Script
            ).options(_sa.joinedload('*'))
            if team_id:
                scripts = scripts.filter(
                    _models.Script.team_id == team_id
                )
            max_elements = scripts.count()
            scripts = scripts.offset(
                page*size
            ).limit(
                size
            ).all()
            return {
                'meta': {
                    'page': page,
                    'max_entries': size,
                    'max_elements': max_elements,
                },
                'data': scripts,
            }

    @_views.post_one()
    @_views.with_model(model=_schemas.Script, include=("team",))
    def post_script(self, post_data, include_data=None):
        data = post_data
        script_name = data.get("name")
        script_cmd = data.get("cmd")
        team_id = data.get("team_id")
        def_opt = data.get("default_options", {})
        if script_name is None:
            raise _views.RestAPIException(
                "No script name is given",
                _views.RESULT_ERROR,
            )
        if script_cmd is None:
            raise _views.RestAPIException(
                "No script command is given",
                _views.RESULT_ERROR,
            )
        if team_id is None:
            raise _views.RestAPIException(
                "No team id is  given",
                _views.RESULT_ERROR,
            )

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
            return script

    @_views.get_one(param="script_id")
    @_views.with_model(output_model=_schemas.Script, include=("team",))
    def get_script(self, script_id, include_data=None):
        with _views.dbsession(self.request) as session:
            script = session.query(
                _models.Script
            ).options(_sa.joinedload('*')).get(script_id)
            if script is None:
                raise _views.RestAPIException(
                    f"Script with id {script_id} not found",
                    _views.RESULT_NOTFOUND,
                )
            return script

    @_views.patch_one(param='script_id')
    @_views.with_model(model=_schemas.Script, include=("team",))
    def update_script(self, script_id, post_data, include_data=None):
        data = post_data
        team_id = data.get("team_id")
        status = data.get("status")
        cmd = data.get("script")
        name = data.get("name")
        with _views.dbsession(self.request) as session:
            script = session.query(
                _models.Script
            ).options(_sa.joinedload('*')).get(script_id)
            if script is None:
                raise _views.RestAPIException(
                    f"Script with id {script_id} not found",
                    _views.RESULT_NOTFOUND,
                )
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

        return script

    @_views.delete_one(param='script_id')
    @_views.with_model(output_model=_schemas.Script, include=("team",))
    def archive_script(self, script_id, include_data=None):
        with _views.dbsession(self.request) as session:
            script = session.query(
                _models.Script
            ).options(_sa.joinedload('*')).get(script_id)
            if script is None:
                raise _views.RestAPIException(
                    f"Script with id {script_id} not found",
                    _views.RESULT_NOTFOUND,
                )
            script.status = "ARCHIVED"
            session.commit()
            session.refresh(script)
            script.team.id
        return script


class ScriptName(_views.BaseResource):
    NAME = 'scripts/name'

    @_views.get_one(description="get name of script", param="script_name")
    @_views.with_model(output_model=_schemas.Script)
    def get_script(self, script_name, include_data=False, **kwargs):
        additional = {}
        if include_data:
            additional["include_data"] = ("team",)

        with _views.dbsession(self.request) as session:
            script = session.query(
                _models.Script
            ).filter_by(name=script_name).options(_sa.joinedload('*')).all()
            if script:
                return script[0]

            raise _views.RestAPIException(
                f"Script with id {script_name} not found",
                _views.RESULT_NOTFOUND
            )


def includeme(config):
    Scripts.init_handler(config)
    ScriptName.init_handler(config)
