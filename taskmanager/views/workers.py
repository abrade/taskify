# -*- coding: utf-8 -*-

import logging as _logging
import json as _json

import pyramid.view as _view

import taskmanager.views as _views
import taskmanager.models as _models
import taskmanager.models.schemas as _schemas

_log = _logging.getLogger(__name__)


@_view.view_defaults(route_name="all_workers")
class Workers(object):
    def __init__(self, request):
        self.request = request


    @_view.view_config(request_method="GET", renderer="json")
    def get(self):
        with _views.dbsession(self.request) as session:
            workers = session.query(
                _models.Worker
            ).all()
            return {
                "result": _views.RESULT_OK,
                "data": _schemas.Worker(many=True).dump(workers).data,
            }

    @_view.view_config(request_method="POST", renderer="json")
    def post(self):
        #worker_name = self.request.params.get("name")
        try:
            data = self.request.json
        except _json.decoder.JSONDecodeError as decode_error:
            return {
                "result": _views.RESULT_ERROR,
                "error": decode_error.msg,
                "data": None,
            }
        worker_name = data.get("name")
        if worker_name is None:
            return {
                "result": _views.RESULT_ERROR,
                "error": "No name is given",
                "data": None,
            }
        with _views.dbsession(self.request) as session:
            worker = _models.Worker()
            worker.name = worker_name
            worker.state = "OFFLINE"
            session.add(worker)
            session.commit()
            session.refresh(worker)

            return {
                "result": _views.RESULT_OK,
                "data": _schemas.Worker().dump(worker).data,
            }

    @_view.view_config(route_name="specific_worker", request_method="GET", renderer="json")
    def get_one(self):
        worker_id = self.request.matchdict.get("id")
        with _views.dbsession(self.request) as session:
            worker = session.query(
                _models.Worker
            ).get(worker_id)
            if worker is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Worker with id {worker_id} not found",
                    "data": None,
                }
            return {
                "result": _views.RESULT_OK,
                "data": _schemas.Worker().dump(worker).data,
            }


def includeme(config):
    config.add_route("all_workers", "/workers")
    config.add_route("specific_worker", "/workers/:id")
