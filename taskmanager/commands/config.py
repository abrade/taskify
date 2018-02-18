# -*- coding: utf-8 -*-

import os as _os
import configparser as _cp


def get_config():
    cfg_parser = _cp.ConfigParser()
    cfg_parser.read(
        [_os.path.expanduser('~/.taskmanager.conf'),
         '/etc/taskmanager.conf']
    )
    return dict(cfg_parser["client"])
