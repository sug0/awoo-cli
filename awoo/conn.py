from os import environ, sep
from urllib import urlencode
from json import load as load_config
from httplib import HTTPSConnection as _https, HTTPConnection as _http

# load config from package dir
cfg = None

try:
    with open('config.json') as f:
        cfg = load_config(f)
        f.close()
except IOError:
    with open('%s%s%s' % (environ.get('HOME'), sep, '.awoo.json')) as f:
        cfg = load_config(f)
        f.close()

_conn = _https if cfg['use_ssl'] else _http

def get(path, headers=None):
    c = _conn(cfg['host'], cfg['port'])

    if headers:
        c.request('GET', path, None, headers)
    else:
        c.request('GET', path)

    return c.getresponse()

def get_with_params(path, params, headers=None):
    params = urlencode(params)
    c = _conn(cfg['host'], cfg['port'])

    if headers:
        c.request('GET', '%s?%s' % (path, params), None, headers)
    else:
        c.request('GET', path, params)

    return c.getresponse()

def post(path, params, headers=None):
    params = urlencode(params)
    c = _conn(cfg['host'], cfg['port'])

    if headers:
        c.request('POST', path, params, headers)
    else:
        c.request('POST', path, params)

    return c.getresponse()

def head(path, headers=None):
    c = _conn(cfg['host'], cfg['port'])

    if headers:
        c.request('HEAD', path, None, headers)
    else:
        c.request('HEAD', path)

    return c.getresponse()

def get_path(uri):
    i = 0
    n = 0

    while n != -1 and i != 4:
        n = uri.find('/')
        uri = uri[n+1:]
        i += 1

    return '/%s' % uri
