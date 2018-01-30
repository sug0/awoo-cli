import conn
from re import search
from json import loads as jload

# httplib exceptions won't be caught

CLIENT_HEADERS = {
    'Client': 'https://github.com/sugoiuguu/awoo-cli',
    'User-Agent': 'https://github.com/sugoiuguu/awoo-cli',
}

class AwooException(Exception):
    pass

def post_reply(board, parent, content):
    if len(content.decode('utf-8')) > 500:
        raise AwooException('Post too long (over 500 characters).')

    params = {
        'content': content,
        'board': board,
        'parent': parent
    }

    if conn.post('/reply', params, CLIENT_HEADERS).status != 200:
        h = conn.cfg['host']
        p = conn.cfg['port']
        raise AwooException('Failed to post reply to %s:%d' % (h, p))

def new_thread(board, title, comment):
    if len(comment.decode('utf-8')) > 500 or len(title.decode('utf-8')) > 500:
        raise AwooException('Post too long (over 500 characters).')

    params = {
        'comment': comment,
        'board': board,
        'title': title 
    }

    path = conn.get_path(conn.post('/post', params, CLIENT_HEADERS).getheader('Location'))

    return '/%s/%s' % (board, search(r'\d+', path).group(0))

def thread_exists(thread_id):
    rsp = conn.head('/api/v2/thread/%d/replies' % thread_id, CLIENT_HEADERS)
    return rsp.status == 200

def get_boards():
    return eval(conn.get('/api/v2/boards', CLIENT_HEADERS).read())

def get_board_description(board):
    rsp = conn.get('/api/v2/board/%s/detail' % board, CLIENT_HEADERS)

    if rsp.status != 200:
        return None
    else:
        return jload(rsp.read())

def get_threads(board, page=0):
    rsp = conn.get_with_params('/api/v2/board/%s' % board, {'page': page}, CLIENT_HEADERS)

    if rsp.status != 200:
        return None
    else:
        return jload(rsp.read())

def get_thread_replies(thread_id):
    rsp = conn.get('/api/v2/thread/%d/replies' % thread_id, CLIENT_HEADERS)

    if rsp.status != 200:
        return None
    else:
        return jload(rsp.read())

def get_thread_metadata(thread_id):
    rsp = conn.get('/api/v2/thread/%d/metadata' % thread_id, CLIENT_HEADERS)

    if rsp.status != 200:
        return None
    else:
        return jload(rsp.read())

def search(board, terms, advanced=False):
    path = '/api/v2/search' if not advanced else '/api/v2/advanced_search'
    params = {'board_select': board, 'search_text': terms}
    rsp = conn.post(path, params, CLIENT_HEADERS)

    if rsp.status != 200:
        print rsp.reason
        print rsp.msg
        return None
    else:
        return jload(rsp.read())
