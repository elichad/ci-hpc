#!/usr/bin/python
# author: Jan Hybs

import os
from copy import deepcopy

import yaml
import re

from utils.logging import logger

_configure_object_regex = re.compile('<([a-zA-Z0-9_\.-]+)(\|[a-zA-Z_]+)?>')
_configure_object_dict = dict(s=str,i=int,f=float,b=bool)


class Config(object):
    """
    Class which loads a .config.yaml file which should be located somewhere in a parent directory
    """
    _instance = None
    _hostname = None
    _cfg = dict()

    @classmethod
    def get(cls, *args, **kwargs):
        if not cls._instance:
            from utils.glob import global_configuration
            cls.init(global_configuration.cfg_secret_path)

        return cls._instance._get(*args, **kwargs)

    @classmethod
    def hostname(cls):
        if not cls._hostname:
            import platform
            cls._hostname = platform.node()
            logger.info('Determined hostname as "%s"', cls._hostname)
        return cls._hostname

    @classmethod
    def init(cls, config_location=None):
        if cls._instance:
            return cls._instance

        if config_location is None:
            current = 0
            max_limit = 10
            root = os.path.dirname(__file__)

            config_file = os.path.join(root, 'secret.yaml')
            while current < max_limit:
                config_file = os.path.join(root, 'secret.yaml')
                current += 1
                if os.path.exists(config_file):
                    break
                root = os.path.dirname(root)
        else:
            config_file = config_location

        cls._instance = Config()
        try:
            cls._cfg = yaml.load(open(config_file, 'r').read()) or dict()
        except Exception as e:
            logger.warn_exception('Failed to load/parse %s configuration file, will use empty dict', config_file)
            logger.warn('You may want to create this file in order to use database connection')
            cls._cfg = dict()
        return cls._instance

    def _get(self, key=None, default=None):
        """
        :rtype: dict or list or string or int or bool
        """
        self.__class__.init()
        cfg_copy = deepcopy(self.__class__._cfg)
        if key is None:
            return cfg_copy

        keys = str(key).split('.')
        if len(keys) == 1:
            return cfg_copy.get(key, default)

        r = cfg_copy
        for k in keys:
            r = r.get(k, {})
        return r

    def _set(self, key, value):
        """
        :rtype: dict or list or string or int or bool
        """
        self.__class__.init()
        self.__class__._cfg[key] = value
        return value

    def __getitem__(self, item):
        return self.get(item)

    def __repr__(self):
        cfg = self.__class__._cfg.copy()
        try:    cfg['pymongo']['password'] = '---HIDDEN---'
        except: pass
        return yaml.dump(cfg, indent=4)


def yaml_load(s):
    return yaml.load(s)


def read_file(path, default=''):
    if os.path.exists(path):
        with open(path, 'r') as fp:
            return fp.read()
    else:
        return default


def load_config(path, replace=True, hostname_conditions=True):
    if not hostname_conditions:
        return yaml_load(read_file(path, default='{}'))
    obj = yaml_load(read_file(path, default='{}'))

    # grab hostname
    hostname = Config.hostname()

    result = dict()
    simple_ones = {k: v for k,v in obj.items() if not isinstance(v, dict)}
    complex_ones = {k: v for k,v in obj.items() if isinstance(v, dict)}

    # add simple variables
    result.update(simple_ones)

    for k, other_dict in complex_ones.items():
        regex = k.replace('.', '\.').replace('*', '.*')

        # we found our hostname match
        if re.match(regex, hostname):
            logger.debug('setting conditional variables (hostname %s matches definition %s)', hostname, k)
            result.update(other_dict)
            return result
    return result


def configure_file(path, variables, convert=yaml_load, start='<', stop='>'):
    content = read_file(path)
    for k, v in variables.items():
        content = content.replace('%s%s%s' % (start, k, stop), v)

    return convert(content)


def configure_string(string, vars):
    result = configure_object(dict(str=string), vars)
    return result.get('str')


def configure_object(obj, vars):
    """
    Configure given object (replaces placeholders <KEY> with VALUE contained in a given vars)
        by default, everything is converted to string, to change conversion type use syntax:
        <KEY|i> to convert value to int
        <KEY|f> to convert value to float
        <KEY|s> to convert value to string (default)
    :type obj: dict
    :type vars: dict
    """
    if not vars:
        return obj

    def get_property(obj, val, default=None):
        """
        :type val: str
        :type obj: dict
        """
        root = obj
        for k in val.split('.'):
            try:
                if isinstance(root, dict):
                    root = root[k]
                else:
                    root = getattr(root, k)
            except:
                return default
        return root

    def configure_item(value, vars):
        matches = _configure_object_regex.findall(str(value))
        if matches:
            value = str(value)
            for key, dtype in matches:
                orig = '<%s%s>' % (key, dtype)
                value = _configure_object_dict.get(dtype[1:], str)(value.replace(orig, str(get_property(vars, key))))
        return value

    obj_copy = deepcopy(obj)
    for k, v in obj_copy.items():
        if isinstance(v, list):
            for i in range(len(v)):
                v[i] = configure_item(v[i], vars)
        elif isinstance(v, dict):
            configure_object(v, vars)
        else:
            obj_copy[k] = configure_item(v, vars)
    return obj_copy
