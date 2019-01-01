# -*- coding: utf-8 -*-

import logging as _logging

import sqlalchemy.orm as _sa

import taskmanager.views as _views
import taskmanager.models as _models
import taskmanager.models.schemas as _schemas

_log = _logging.getLogger(__name__)


def get_worker(worker_id, session, use_default_worker=False):
    """ Helper function to get worker by name

    Args:
        worker_name (str): name of worker
        session (DBSession): the sqlalchemy db session
        use_default_worker (bool, optional): flag to use default
            worker unless no worker found, default to False

    Returns:
        Worker: The sql alchemy model if worker is found else None
    """
    result = session.query(
        _models.WorkerQueue
    ).get(worker_id)

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


def get_script_by_id(script_id, session):
    return session.query(
        _models.Script
    ).get(script_id)


def get_script(script_name, session):
    """ Helper function to get script

    Args:
        script_name (list): the script name
        session (DBSession): the sqlalchemy db session

    Returns:
        Script: The sql alchemy model if script was found else None
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


class Tasks(_views.BaseResource):
    NAME = "tasks"

    @_views.post_one()
    @_views.with_model(model=_schemas.Tasks, include=("",))
    def post_task(self, post_data):
        data = post_data
        _log.info("Data: {}".format(data))
        title = data.get("title")
        worker_id = data.get("worker")
        script_id = [data.get("script")]
        options = data.get("options", {})
        parent_id = data.get("parent_id")
        depends = data.get("depends", [])
        use_def_opt = data.get("use_default_opt", False)
        scheduled_by = data.get("scheduled_by", "")

        _log.debug(f"Depends: {depends}")
        with _views.dbsession(self.request) as session:
            # request.registry.settings.get('use_default_worker', False)
            worker = get_worker(worker_id, session)
            if not worker:
                raise _views.RestAPIException(
                    "Couldn't find worker",
                    _views.RESULT_ERROR
                )

            script = get_script_by_id(script_id, session)
            if not script:
                raise _views.RestAPIException(
                    "Couldn't find script",
                    _views.RESULT_ERROR,
                )

            if not script.is_active:
                raise _views.RestAPIException(
                    "Script is not ACTIVE",
                    _views.RESULT_ERROR,
                )

            if use_def_opt:
                # update options with default options
                def_opt = script.default_options
                options.update(def_opt)

            task = _models.Task(
                title,
                script.id,
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

            return task

    @_views.get_all()
    @_views.with_model(output_model=_schemas.Tasks, include=("script", "worker", "script.team", "depends"))
    @_views.with_links
    def get_tasks(self, state="ALL", page=0, size=20, script=None, worker=None, team=None, include_data=None):
        max_entries = int(size)
        state_filter = get_states(state)
        _log.debug(f"Params: {self.request.params}")
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
            query = tasks.order_by(
                _models.Task.id.desc()
            )
            max_elements = query.count()
            _log.debug("offset : {offset}".format(offset=page*max_entries))
            tasks = query.offset(
                page*max_entries
            ).limit(
                max_entries
            ).options(_sa.joinedload('*')).all()
            # TODO: Hack
            _schemas.Tasks(many=True).dumps(tasks)
            return {
                'meta': {
                    'page': page,
                    'max_entries': max_entries,
                    'max_elements': max_elements,
                },
                'data': tasks,
            }

    @_views.get_one(param="task_id")
    @_views.with_model(output_model=_schemas.Tasks, include=("script", "worker",))
    def get_one(self, task_id, include_data=None):
        with _views.dbsession(self.request) as session:
            task = session.query(
                _models.Task
            ).get(task_id)
            if task is None:
                raise _views.RestAPIException(
                    f"Task with id {task_id} not found",
                    _views.RESULT_NOTFOUND,
                )
            # TODO: Hack
            _schemas.Tasks().dumps(task)
            return task

    @_views.patch_one(param="task_id")
    @_views.with_model(model=_schemas.Tasks, include=("script", "worker",))
    def update_task(self, task_id, post_data, include_data=None):
        data = post_data
        worker_id = data.get("worker")
        script_id = data.get("script")
        options = data.get("options")
        with _views.dbsession(self.request) as session:
            task = session.query(
                _models.Task
            ).get(task_id)
            if task is None:
                raise _views.RestAPIException(
                    f"Task with id {task_id} not found",
                    _views.RESULT_NOTFOUND,
                )
            if worker_id:
                task.worker_id = worker_id
            if script_id:
                task.script_id = script_id
            if options:
                task.options.update(options)

            session.commit()

            return task

    @_views.delete_one(param="task_id")
    @_views.with_model(output_model=_schemas.Tasks, include=("script", "worker"))
    def delete_task(self, task_id, include_data=None):
        with _views.dbsession(self.request) as session:
            task = session.query(
                _models.Task
            ).get(task_id)
            if task is None:
                raise _views.RestAPIException(
                    f"Task with id {task_id} not found",
                    _views.RESULT_NOTFOUND,
                )

            task.state = "DELETED"
            session.commit()

            return task


class TaskLogs(_views.BaseResource):
    NAME = "tasklogs"

    @_views.get_all()
    @_views.with_model(output_model=_schemas.TaskLog, include=("worker",))
    def get_task_log(self, task=None):
        with _views.dbsession(self.request) as session:
            task_logs = session.query(
                _models.TaskLog
            ).filter(
                _models.TaskLog.task_id == task
            ).all()
            for log in task_logs:
                print("task_logs: {} {} {}".format(
                    log.task_id, log.run, log.state))
            return task_logs


class TaskChildren(_views.BaseResource):
    NAME = "tasks/{task_id}/children"

    @_views.get_all()
    @_views.with_model(output_model=_schemas.Tasks, include=("worker", "script"))
    def get_children(self, task_id):
        with _views.dbsession(self.request) as session:
            task = session.query(
                _models.Task
            ).get(task_id)
            if task is None:
                raise _views.RestAPIException(
                    f"Task with id {task_id} not found",
                    _views.RESULT_NOTFOUND
                )
            return task


class TaskDepends(_views.BaseResource):
    NAME = "tasks/{task_id}/depends"

    @_views.get_all()
    @_views.with_model(output_model=_schemas.Tasks, include=("worker", "script"))
    def get_depends(self, task_id):
        with _views.dbsession(self.request) as session:
            task = session.query(
                _models.Task
            ).get(task_id)
            if task is None:
                raise _views.RestAPIException(
                    f"Task with id {task_id} not found",
                    _views.RESULT_NOTFOUND
                )
            return task.depends


class TaskResult(_views.BaseResource):
    NAME = "tasks/{task_id}/result"

    @_views.get_all()
    def task_result(self, task_id):
        with _views.dbsession(self.request) as session:
            task = session.query(
                _models.Task
            ).get(task_id)
            if task is None:
                raise _views.RestAPIException(
                    f"Task with id {task_id} not found",
                    _views.RESULT_NOTFOUND,
                )
            result = _views.get_result(str(task.id))
            return {
                "result": _views.RESULT_OK,
                "data": {
                    "return_code": result[0],
                    "stdout": result[1],
                    "stderr": result[2],
                }
            }


class TaskState(_views.BaseResource):
    NAME = "tasks/state"

    @_views.get_all()
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


def includeme(config):
    TaskState.init_handler(config)
    Tasks.init_handler(config)
    TaskChildren.init_handler(config)
    TaskDepends.init_handler(config)
    TaskLogs.init_handler(config)
