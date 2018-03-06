# -*- coding: utf-8 -*-

import logging as _logging

import pyramid.view as _view
import pyramid.httpexceptions as _he

_log = _logging.getLogger(__name__)


@_view.notfound_view_config()
def not_found(request):
    return _he.HTTPNotFound("Ressource not found")


@_view.forbidden_view_config()
def forbidden(request):
    return _he.HTTPForbidden("No entry!")
