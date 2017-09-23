import conn
from json import loads as jload

# httplib exceptions won't be caught

class AwooException(Exception):
    pass

def post_reply(board, parent, content):
    if len(content) > 500:
        raise AwooException('Post too long (over 500 characters).')

    params = {
        'content': content,
        'board': board,
        'parent': parent
    }

    if conn.post('/reply', params).status != 200:
        h = conn.cfg['host']
        p = conn.cfg['port']
        raise AwooException('Failed to post reply to %s:%d' % (h, p))

def new_thread(board, title, comment):
    if len(comment) > 500 or len(title) > 500:
        raise AwooException('Post too long (over 500 characters).')

    params = {
        'comment': comment,
        'board': board,
        'title': title 
    }

    return conn.get_path(conn.post('/post', params).getheader('Location'))

def thread_exists(thread_id):
    rsp = conn.head('/api/v2/thread/%d/replies' % thread_id)
    return rsp.status == 200

def get_boards():
    return eval(conn.get('/api/v2/boards').read())

def get_board_description(board):
    rsp = conn.get('/api/v2/board/%s/detail' % board)

    if rsp.status != 200:
        return None
    else:
        return jload(rsp.read())

def get_threads(board, page=0):
    rsp = conn.get_with_params('/api/v2/board/%s' % board, {'page': page})

    if rsp.status != 200:
        return None
    else:
        return jload(rsp.read())

def get_thread_replies(thread_id):
    rsp = conn.get('/api/v2/thread/%d/replies' % thread_id)

    if rsp.status != 200:
        return None
    else:
        return jload(rsp.read())

def get_thread_metadata(thread_id):
    rsp = conn.get('/api/v2/thread/%d/metadata' % thread_id)

    if rsp.status != 200:
        return None
    else:
        return jload(rsp.read())
