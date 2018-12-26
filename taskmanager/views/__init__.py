# -*- coding: utf-8 -*-

import os as _os
import math as _math
import configparser as _cp
import contextlib as _ct
import transaction as _ta
import subprocess as _subprocess
import importlib as _importlib
import functools as _ft
import collections as _collection
import inspect as _inspect

import celery as _celery
import celery.result as _result
import celery.exceptions as _exceptions

import psycopg2 as _psycopg2

import sqlalchemy.orm as _orm
import celery.utils.log as _logging

import taskmanager.models as _models

_log = _logging.get_task_logger(__name__)

RESULT_OK = "OK"
RESULT_ERROR = "ERROR"
RESULT_NOTFOUND = "NOT_FOUND"


class RestAPIException(Exception):
    def __init__(self, message, error_type=RESULT_ERROR):
        super().__init__(message)
        self.error_type = error_type
        self.message = message


celery_app = None

if celery_app is None:
    cfg_parser = _cp.ConfigParser()
    cfg_parser.read(
        [
            _os.path.expanduser('~/.taskmanager.conf'),
            '/etc/taskmanager.conf'
        ]
    )
    celery_config = cfg_parser['celery']
    celery_app = _celery.Celery(**dict(celery_config))
    celery_app.conf.task_default_queue = 'default'
    celery_app.conf.task_queues = []


def get_result(task_id):
    res = _result.AsyncResult(task_id, app=celery_app, timeout=300)
    try:
        return res.get()
    except _exceptions.TimeoutError:
        return {}


@celery_app.task(retry_kwargs={'max_retries': 5})
def start_task(executable, config, options, additional_info=None):
    current_env = _os.environ.copy()
    for k, v in options.items():
        if isinstance(v, int):
            options[k] = str(v)
    current_env.update(options)
    current_env["TASK_ID"] = start_task.request.id
    current_env["PARENT_ID"] = ''
    if additional_info and "parent_id" in additional_info:
        current_env["PARENT_ID"] = str(additional_info.get("parent_id", ""))
    cmd = [executable, config]
    try:
        task = _subprocess.Popen(
            cmd,
            env=current_env,
            shell=True,
            stdout=_subprocess.PIPE,
            stderr=_subprocess.PIPE,
        )
        stdout, stderr = task.communicate()
        if task.returncode != 0:
            _log.info("retry...")
            start_task.retry()
        else:
            return (
                task.returncode,
                stdout.decode('utf-8'),
                stderr.decode('utf-8'),
            )
    except Exception as e:
        _log.error("Something happen .... retry... %r", e)
        start_task.retry()


@celery_app.task(retry_kwargs={'max_retries': 5})
def start_function(function, config, args, additional_info=None):
    print('{}, {}, {}'.format(function, args, additional_info))
    module, func = function.rsplit('.', 1)
    try:
        module = _importlib.import_module(module)
    except ImportError as e:
        return (-1, '', e)

    func = getattr(module, func)
    if func is None:
        return (-1, '', 'Function not found!')
    try:
        if isinstance(args, (list, tuple)):
            ret = func(config, *args)
        elif isinstance(args, dict):
            ret = func(config, **args)
    except Exception as e:
        print('EXCEPTION : %r', e)
        _log.error("Catched exception ... %r", e)
        start_function.retry()

    return (0, ret, '')


@_ct.contextmanager
def dbsession(request):
    settings = request.registry.settings
    engine = _models.get_engine(settings)
    session_factory = _models.get_session_factory(engine)
    db_session = _orm.scoped_session(session_factory)
    yield db_session
    db_session.remove()
    engine.dispose()
    # with _ta.manager:
    #     yield _models.get_tm_session(session_factory, _ta.manager)


@_ct.contextmanager
def get_connection(request):
    settings = request.registry.settings
    yield _psycopg2.connect(settings['sqlalchemy.url'])


def create_links(base_url, page, max_entries, max_elements):
    count = _math.ceil(max_elements / max_entries)
    next_page = page + 1 if (page + 1) < count else count
    prev_page = page - 1 if page - 1 >= 0 else 0
    base_unformat_url = "{}?page[number]={}&page[size]={}"
    return {
        "self": base_unformat_url.format(base_url, page, max_elements),
        "next": base_unformat_url.format(base_url, next_page, max_entries),
        "prev": base_unformat_url.format(base_url, prev_page, max_entries),
        "first": base_unformat_url.format(base_url, 0, max_entries),
        "last": base_unformat_url.format(base_url, count - 1, max_entries),
    }


class BaseResource(object):
    NAME = None

    def __init__(self, request):
        self.request = request

    @classmethod
    def _get_all(cls, config, func):
        cls._define_route(config, func, 'GET')

    @classmethod
    def _get_one(cls, config, func):
        cls._define_route_with_param(config, func, 'GET')

    @classmethod
    def _post_one(cls, config, func):
        cls._define_route(config, func, 'POST')

    @classmethod
    def _patch_one(cls, config, func):
        cls._define_route_with_param(config, func, 'PATCH')

    @classmethod
    def _delete_one(cls, config, func):
        cls._define_route_with_param(config, func, 'DELETE')

    @classmethod
    def _define_route(cls, config, func, req_method):
        resource = func.__resource__
        url = f'/{cls.NAME}'
        name = f'{cls.NAME}/{func.__name__}/{req_method}'
        resource['name'] = name
        print(f"Adding {url} for {name} and {req_method}")
        config.add_route(name, url, request_method=req_method)
        config.add_view(
            view=cls,
            attr=func.__name__,
            route_name=name,
            request_method=req_method,
            renderer='json'
        )

    @classmethod
    def _define_route_with_param(cls, config, func, req_method):
        resource = func.__resource__
        url = f'/{cls.NAME}/{{{resource.get("param")}}}'
        name = f'{cls.NAME}/{func.__name__}/{req_method}'
        resource['name'] = name
        print(f"Adding {url} for {name} and {req_method}")
        config.add_route(name, url, request_method=req_method)
        config.add_view(
            view=cls,
            attr=func.__name__,
            route_name=name,
            request_method=req_method,
            renderer='json'
        )

    @classmethod
    def init_handler(cls, config):
        # route_name = "{base_route}:id".format(base_route=cls.base_route)
        # config.add_view(view=cls, attr='get_one', route_name=route_name, request_method="GET", renderer="json")
        configs = {
            'get_all': cls._get_all,
            'get_one': cls._get_one,
            'post_one': cls._post_one,
            'patch_one': cls._patch_one,
            'delete_one': cls._delete_one,
        }
        for name, method in cls.__dict__.items():
            if not hasattr(method, "__resource__"):
                continue
            resource = method.__resource__
            handler = configs[resource['type']]
            handler(config, method)


def _wrap_func(func):
    if func.__resource__.get('wrapped'):
        return func

    @_ft.wraps(func)
    def wrapper(self, *args, **kwargs):
        # get params
        # load the data
        # need request
        resource = func.__resource__
        req = self.request
        kwargs.update(req.matchdict)
        include_data = False
        for key, value in req.params.items():
            if not value:
                continue
            if key == "page[number]":
                kwargs["page"] = int(value)
            elif key == "page[size]":
                kwargs["size"] = int(value)
            elif key == 'include_data':
                include_data = True
                continue
            else:
                kwargs[key] = value
        input_schema = resource.get('input_model')
        output_schema = resource.get('output_model')

        if input_schema:
            input_data = req.json
            input_data = input_schema().load(input_data).data
            kwargs.update({'post_data': input_data})
        try:
            print(dict(req.params))
            data = func(self, *args, **kwargs)
        except RestAPIException as ex:
            return {
                "result": ex.error_type,
                "error": ex.message,
                "data": None,
            }
        if data is None:
            return {
                "result": RESULT_NOTFOUND,
                "error": "Couldn't find object",
                "data": None,
            }
        with_links = resource.get('with_links')
        result = {
            "result": RESULT_OK,
        }
        if with_links:
            meta = data['meta']
            data = data['data']
            result["meta"] = {"count": meta["max_elements"]}
            result["links"] = create_links(
                req.route_url(resource.get("name")),
                **meta,
            )

        attr = {'many': False}
        if isinstance(data, _collection.Iterable):
            attr['many'] = True
        if include_data:
            attr['include_data'] = resource.get('include')

        if output_schema:
            data = output_schema(**attr).dump(data).data

        result.update(data)
        return result

    func.__resource__['wrapped'] = True
    return wrapper


def get_all(description=None):
    """ decorater for get all """
    def wrapper(func):
        func.__resource__ = func.__dict__.get('__resource__', {})
        func.__resource__.setdefault('description', description)
        func.__resource__.setdefault('type', 'get_all')
        return _wrap_func(func)
    return wrapper


def get_one(description=None, param=None):
    """ decorater for get one """
    def wrapper(func):
        func.__resource__ = func.__dict__.get('__resource__', {})
        func.__resource__.setdefault('description', description)
        func.__resource__.setdefault('param', param)
        func.__resource__.setdefault('type', 'get_one')

        return _wrap_func(func)
    return wrapper


def post_one(description=None):
    """ decorater for post """
    def wrapper(func):
        func.__resource__ = func.__dict__.get('__resource__', {})
        func.__resource__.setdefault('description', description)
        func.__resource__.setdefault('type', 'post_one')

        return _wrap_func(func)
    return wrapper


def patch_one(description=None, param=None):
    """ decorater for post """
    def wrapper(func):
        func.__resource__ = func.__dict__.get('__resource__', {})
        func.__resource__.setdefault('description', description)
        func.__resource__.setdefault('param', param)
        func.__resource__.setdefault('type', 'patch_one')

        return _wrap_func(func)
    return wrapper


def delete_one(description=None, param=None):
    """ decorater for delete """
    def wrapper(func):
        func.__resource__ = func.__dict__.get('__resource__', {})
        func.__resource__.setdefault('description', description)
        func.__resource__.setdefault('param', param)
        func.__resource__.setdefault('type', 'delete_one')

        return _wrap_func(func)
    return wrapper


def with_model(model=None, input_model=None, output_model=None, include=None):
    """ decorater for input model"""
    if model and (input_model or output_model):
        raise ValueError("""Model and input or output model are defined.
Model defines in- and output model. If you need to specify different input and output models, use input_model and output_model.
""")
    def wrapper(func):
        func.__resource__ = func.__dict__.get('__resource__', {})
        in_model = input_model
        out_model = output_model
        if model:
            in_model = out_model = model
        func.__resource__.setdefault('input_model', in_model)
        func.__resource__.setdefault('output_model', out_model)
        func.__resource__.setdefault('include', include)

        return _wrap_func(func)
    return wrapper


def with_return(http_code=200, description=None):
    """ decorater for input model"""
    def wrapper(func):
        func.__resource__ = func.__dict__.get('__resource__', {})
        func.__resource__.setdefault('return_codes', [])
        func.__resource__['return_codes'].append((http_code, description))

        return _wrap_func(func)
    return wrapper


def with_links(func):
    func.__resource__ = func.__dict__.get('__resource__', {})
    func.__resource__.setdefault('with_links', True)
    return _wrap_func(func)
