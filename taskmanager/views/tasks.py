# -*- coding: utf-8 -*-

import json as _json
import logging as _logging

import pyramid.view as _view

import taskmanager.views as _views
import taskmanager.models as _models
import taskmanager.models.schemas as _schemas

_log = _logging.getLogger(__name__)


def get_worker(worker_name, session, use_default_worker=False):
    """ Helper function to get worker by name

    Args:
        worker_name (str): name of worker
        session (object): the sqlalchemy db session
        use_default_worker (bool, optional): flag to use default
            worker unless no worker found, default to False

    Returns:
        object: The sql alchemy model if worker is found else None
    """
    result = session.query(
        _models.WorkerQueue
    ).filter(
        _models.WorkerQueue.name == worker_name
    ).first()

    if not result and use_default_worker:
        _log.info("Worker not found, use default...")
        result = session.query(
            _models.WorkerQueue
        ).filter(
            _models.WorkerQueue.name == "default"
        ).first()
    elif not result:
        _log.info("Worker not found")
        return

    return result


def get_script(script_name, session):
    """ Helper function to get script

    Args:
        script_name (str): the script name
        session (object): the sqlalchemy db session

    Returns:
        object: The sql alchemy model if script was found else None
    """
    return session.query(
        _models.Script
    ).filter(
        _models.Script.name.in_(script_name)
    ).all()


def get_scripts(team_id, session):
    return session.query(
        _models.Script
    ).filter(
        _models.Script.team_id == team_id
    ).all()


def get_states(state_filter):
    lookup = {
        "ALL": None,
        "ACTIVE": ["PRERUN", "STARTED"],
    }

    return lookup.get(state_filter, [state_filter])


@_view.view_defaults(route_name="tasks", renderer="json")
class Tasks(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(request_method="POST")
    def post_task(self):
        try:
            data = self.request.json
        except _json.decoder.JSONDecodeError as decode_error:
            return {
                "result": "error",
                "error": decode_error.msg
            }
        _log.info("Data: {}".format(data))
        title = data.get("title")
        worker_name = data.get("worker")
        script_name = [data.get("script")]
        options = data.get("options", {})
        parent_id = data.get("parent_id")
        depends = data.get("depends", [])
        use_def_opt = data.get("use_default_opt", False)
        scheduled_by = data.get("scheduled_by", "")

        _log.debug(f"Depends: {depends}")
        with _views.dbsession(self.request) as session:
            # request.registry.settings.get('use_default_worker', False)
            worker = get_worker(worker_name, session)
            if not worker:
                return {
                    "result": _views.RESULT_ERROR,
                    "error": "Couldn't find worker"
                }

            script = get_script(script_name, session)
            if not script:
                return {
                    "result": _views.RESULT_ERROR,
                    "error": "Couldn't find script"
                }

            if use_def_opt:
                # update options with default options
                def_opt = script.default_options
                options.update(def_opt)

            task = _models.Task(
                title,
                script[0].id,
                worker.id,
                parent_id,
                "PRERUN",
                options,
                scheduled_by=scheduled_by,
            )
            session.add(task)
            session.commit()
            for depend in depends:
                task_depend = _models.TaskDepends(
                    task.id,
                    int(depend),
                )
                session.add(task_depend)
            session.commit()

            return {
                "result": _views.RESULT_OK,
                "id": task.id,
                **_schemas.Tasks().dump(task).data
            }

    @_view.view_config(request_method="GET")
    def get_tasks(self):
        state_filter = self.request.params.get("state", "ALL")
        page = int(self.request.params.get("page", 1))
        max_entries = int(self.request.params.get("limit", 20))
        script = self.request.params.getall("script")
        worker = self.request.params.getall("worker")
        team = self.request.params.get("team")
        include_data = self.request.params.get("include_data")

        page = page - 1
        state_filter = get_states(state_filter)
        _log.debug(f"State filter: {state_filter}")
        _log.debug(f"page {page}")
        _log.debug(f"max_entries {max_entries}")
        _log.debug(f"script {script}")
        with _views.dbsession(self.request) as session:
            tasks = session.query(
                _models.Task
            )
            if state_filter:
                tasks = tasks.filter(
                    _models.Task.state.in_(state_filter)
                )
            if script:
                script_obj = get_script(script, session)
                script_ids = [script.id for script in script_obj]
                if script_obj:
                    tasks = tasks.filter(
                        _models.Task.script_id.in_(script_ids)
                    )
            if worker:
                worker = [int(worker_id) for worker_id in worker]
                tasks = tasks.filter(
                    _models.Task.worker_id.in_(worker)
                )
            if team:
                scripts = get_scripts(team, session)
                tasks = tasks.filter(
                    _models.Task.script_id.in_(
                        tuple(script.id for script in scripts))
                )
            tasks = tasks.order_by(
                _models.Task.id.desc()
            ).offset(
                page*max_entries
            ).limit(
                max_entries
            ).all()
            additional = {}
            if include_data:
                additional["include_data"] = ("script", "worker")
            return {
                "result": _views.RESULT_OK,
                **_schemas.Tasks(**additional).dump(tasks, many=True).data,
            }

    @_view.view_config(route_name="tasks_state", request_method="GET")
    def tasks_state(self):
        with _views.get_connection(self.request) as connection:
            stmt = """
            SELECT
                state, count(1)
            FROM
                tasks
            GROUP BY
                state
            """
            result = {
                "SUCCEED": 0,
                "FAILED": 0,
                "FAILED-ACKED": 0,
                "PRERUN": 0,
                "STARTED": 0,
                "RETRIED": 0,
                "ALL": 0,
            }
            cur = connection.cursor()
            cur.execute(stmt)
            db_result = dict(cur.fetchall())
            result.update(db_result)
            all_tasks = sum(db_result.values())
            result["ALL"] = all_tasks
            return {
                "result": _views.RESULT_OK,
                "data": {
                    "type": "state",
                    "attributes": {
                        **result
                    },
                    "id": 1,
                }
            }


@_view.view_defaults(route_name="specific_task", renderer="json")
class Task(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(request_method="GET")
    def get_one(self):
        task_id = self.request.matchdict.get("id")
        with _views.dbsession(self.request) as session:
            task = session.query(
                _models.Task
            ).get(task_id)
            if task is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Task with id {task_id} not found",
                    "data": None,
                }
            return {
                "result": _views.RESULT_OK,
                **_schemas.Tasks().dump(task).data,
            }

    @_view.view_config(request_method="PATCH")
    def update_task(self):
        task_id = self.request.matchdict.get("id")
        try:
            data = self.request.json
        except _json.decoder.JSONDecodeError as decode_error:
            return {
                "result": "error",
                "error": decode_error.msg
            }
        worker_id = data.get("worker")
        script_id = data.get("script")
        options = data.get("options")
        with _views.dbsession(self.request) as session:
            task = session.query(
                _models.Task
            ).get(task_id)
            if task is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Task with id {task_id} not found",
                    "data": None,
                }
            if worker_id:
                task.worker_id = worker_id
            if script_id:
                task.script_id = script_id
            if options:
                task.options.update(options)

            session.commit()

            return {
                "result": _views.RESULT_OK,
                **_schemas.Task().dump(task).data,
            }

    @_view.view_config(request_method="DELETE")
    def delete_task(self):
        task_id = self.request.matchdict.get("id")
        with _views.dbsession(self.request) as session:
            task = session.query(
                _models.Task
            ).get(task_id)
            if task is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Task with id {task_id} not found",
                    "data": None,
                }

            task.state = "DELETED"
            session.commit()

            return {
                "result": _views.RESULT_OK,
                **_schemas.Task().dump(task).data,
            }

    @_view.view_config(route_name="task_result", request_method="GET")
    def task_result(self):
        task_id = self.request.matchdict.get("id")
        with _views.dbsession(self.request) as session:
            task = session.query(
                _models.Task
            ).get(task_id)
            if task is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Task with id {task_id} not found",
                    "data": None,
                }
            result = _views.get_result(str(task.id))
            return {
                "result": _views.RESULT_OK,
                "data": {
                    "return_code": result[0],
                    "stdout": result[1],
                    "stderr": result[2],
                }
            }


@_view.view_defaults(route_name="specific_task_logs", renderer="json")
class TaskLogs(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(route_name="task_logs", request_method="GET")
    def get_task_log(self):
        task_id = self.request.params.get("task")
        include_data = self.request.params.get("include_data")
        additional = {}
        if include_data:
            additional["include_data"] = ("worker",)
        with _views.dbsession(self.request) as session:
            task_logs = session.query(
                _models.TaskLog
            ).filter(
                _models.TaskLog.task_id == task_id
            ).all()
            for log in task_logs:
                print("task_logs: {} {} {}".format(
                    log.task_id, log.run, log.state))
            data = _schemas.TaskLog(
                **additional).dump(task_logs, many=True).data
            return {
                "result": _views.RESULT_OK,
                **data
            }


@_view.view_defaults(route_name="task_children", renderer="json")
class TaskChildren(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(request_method="GET")
    def get_children(self):
        task_id = self.request.matchdict.get("id")
        include_data = self.request.params.get("include_data")
        additional = {}
        if include_data:
            additional["include_data"] = ("worker", "script")
        with _views.dbsession(self.request) as session:
            task = session.query(
                _models.Task
            ).get(task_id)
            if task is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Task with id {task_id} not found",
                    "data": None,
                }
            return {
                "result": _views.RESULT_OK,
                **_schemas.Tasks().dump(task.children, many=True).data,
            }




def includeme(config):
    config.add_route("tasks", "/tasks")
    config.add_route("tasks_state", "/tasks/state")
    config.add_route("specific_task", "/tasks/:id")
    config.add_route("task_result", "/tasks/:id/result")
    config.add_route("task_logs", "/tasklogs")
    config.add_route("task_children", "/tasks/:id/children")
