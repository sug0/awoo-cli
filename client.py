import awoo
import colors
import utils.database as database

from re import compile as re_compile, M as re_M
from utils.colortrans import rgb2short
from datetime import datetime
from subprocess import Popen, PIPE
from sys import stdin, stdout, exit
from os import environ, name as os_name, system, sep, remove

# 'more' is usually present in all relevant OSes
MORE = 'more.com' if os_name == 'nt' else 'more'
PAGER = environ.get('PAGER') or MORE
EDITOR = environ.get('EDITOR') or ('notepad.exe' if os_name == 'nt' else 'vi')
CLEAR = 'cls' if os_name == 'nt' else 'clear'
TMP_ = environ.get('TMP') if os_name == 'nt' else '/tmp'
DB_PATH = '%s%s%s' % (environ.get('HOME') or environ.get('HOMEPATH'), sep, '.awoo_threads_pinned.gz')
DB = database.load(DB_PATH) or []
PROMPT = colors.red('>>>')
RE_1 = (re_compile(r'(^>[^>].*$)', re_M), colors.red(r'\1'))
RE_2 = (re_compile(r'(>>\d+)'), colors.cyan(r'\1'))
BOARD_BLACKLIST = []

def TMP(path):
    return '%s%s%s' % (TMP_, sep, '__%s__' % path)

# need a mutable object to change
# the currently selected board or reply
class CurrentBoard:
    def __init__(self):
        default = awoo.get_board_description(awoo.conn.cfg['default_board'])

        if not default:
            raise awoo.AwooException()

        self.default = default['name']
        self.board = self.default
        self.desc = default['desc']

        self.last_cmd = None

    def cd(self, board=None):
        board = board if board else self.default
        board = awoo.get_board_description(board)

        if not board:
            raise awoo.AwooException()

        self.board = board['name']
        self.desc = board['desc']

def flush_database():
    database.write(DB, DB_PATH)

def write_new_thr_database(thr, description):
    DB.append((thr, description))
    flush_database()

def remove_thr_database(thr):
    [DB.remove(t) for t in DB if t[0] == thr]
    flush_database()

def remove_all_thr_database():
    del DB[:]
    flush_database()

def less(data):
    process = Popen([PAGER], stdin=PIPE)
    data = data if isinstance(data, str) else str(data.encode('utf-8'))

    try:
        process.stdin.write(data)
        process.communicate()
        process.wait()
    except IOError:
        pass

def edit(file):
    process = Popen([EDITOR, file])
    process.communicate()
    process.wait()

def edit_(file):
    edit(file)

    try:
        with open(file, 'r') as f:
            reply = f.read().rstrip()
            f.close()
    except IOError:
        return None

    try:
        remove(file)
    except OSError:
        print "Temp file is already removed, skipping step."

    return reply

def safe_int(n):
    try:
        return int(n)
    except ValueError:
        return None

def get_date(t):
    return datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')

def color_hash(h):
    _c = None

    try:
        _c, _ = rgb2short('#%s' % h)
        _c = int(_c)
    except:
        _c = hash(h) % 256

    return colors.color(h, fg=_c)

def cap_or_hash(post):
    return post.get('capcode') or post['hash']

def comment_or_blankfag(post):
    comment = post['comment']

    if comment:
        comment = RE_1[0].sub(RE_1[1], comment.replace('\r\n', '\n'))
        comment = RE_2[0].sub(RE_2[1], comment)
        return comment
    else:
        return colors.red('[[BLANKFAG]]')

def title_or_blankfag(thread):
    return thread['title'] or '[[BLANKFAG]]'

def color_reply_count(thread):
    if thread['is_locked']:
        return colors.red('%dL' % thread['number_of_replies'])
    else:
        return colors.yellow('%d' % thread['number_of_replies'])

def eval_cmd(sel, toks):
    try:
        CMD_DICT[toks[0]](sel, toks)

        if toks[0] != 'r' and toks[0] != '!!' and toks[0] != 'repeat':
            sel.last_cmd = toks
    except KeyError:
        if toks[0]:
            print 'Command "%s" not available. Try "help".' % toks[0]

def threads_format(sel, page, threads):
    ppt = PROMPT
    bar = colors.cyan('--------------------------------------------------')
    fmt = '\n%s\n%s /%s/ - %s\n%s\n\n' % (bar, ppt, colors.cyan(sel.board), colors.green(sel.desc), bar)

    if sel.board == sel.default and BOARD_BLACKLIST:
        threads = [thr for thr in threads if 'title' in thr and thr['board'] not in BOARD_BLACKLIST]
    else:
        threads = [thr for thr in threads if 'title' in thr]

    threads = sorted(threads, key=lambda thr: thr['last_bumped'], reverse=True)

    for thr in threads:
        fmt += "%s [%s] (%s) %s [%s] [%s]\n%s\n\n%s\n--------------------------------------------------\n\n" % (
            '%s. %s' % (colors.red('No'), colors.green('%d' % thr['post_id'])),
            color_hash(cap_or_hash(thr)),
            colors.yellow(get_date(thr['date_posted'])),
            colors.green(title_or_blankfag(thr)),
            color_reply_count(thr),
            colors.red(thr['board']),
            comment_or_blankfag(thr),
            colors.cyan('Last bumped on: %s' % get_date(thr['last_bumped']))
        )

    return '%s%s\n' % (fmt, colors.green('Page number: %d' % page))

def replies_format(replies):
    fmt = "%s [%s] (%s) %s [%s] [%s]\n%s\n\n--------------------------------------------------\n\n" % (
        '%s. %s' % (colors.red('No'), colors.green('%d' % replies[0]['post_id'])),
        color_hash(cap_or_hash(replies[0])),
        colors.yellow(get_date(replies[0]['date_posted'])),
        colors.green(title_or_blankfag(replies[0])),
        color_reply_count(replies[0]),
        colors.red(replies[0]['board']),
        comment_or_blankfag(replies[0])
    )

    for r in replies[1:]:
        fmt += "%s [%s] (%s)\n%s\n\n--------------------------------------------------\n\n" % (
            '%s. %s' % (colors.red('No'), colors.green('%d' % r['post_id'])),
            color_hash(cap_or_hash(r)),
            colors.yellow(get_date(r['date_posted'])),
            comment_or_blankfag(r)
        )

    fmt += colors.cyan('Last bumped on: %s' % get_date(replies[0]['last_bumped']))

    return fmt

def cmd_help(_, toks):
    """\
    Print all the commands available.

    Usage: h|help
           h|help [command]"""

    if len(toks) < 2:
        fmt = ''

        for cmd in sorted(CMD_DICT):
            fmt += ('%s:\n%s\n\n' % (cmd, CMD_DICT[cmd].__doc__)
                or 'No help available for "%s".' % cmd)

        less(fmt)
    else:
        try:
            less('%s:\n%s' % (toks[1], CMD_DICT[toks[1]].__doc__)
                or 'No help available for "%s".' % toks[1])
        except KeyError:
            print 'Command "%s" not available.' % toks[1]

def cmd_clear(_, _0):
    """\
    Clears the terminal window.

    Usage: cls|clear"""

    system(CLEAR)

def cmd_quit(_, _0):
    """\
    Exits the client.

    Usage: q|quit|exit"""

    exit(0)

def cmd_get_boards(_, _0):
    """\
    Fetches the board list.

    Usage: ls|gb|get_boards"""

    for board in awoo.get_boards():
        stdout.write('%s  ' % board)

    stdout.write('\n')

def cmd_get_threads(sel, toks):
    """\
    Fetches the thread list from a board.

    Usage: gt|get_threads
           gt|get_threads [page number]"""

    page = 0 if len(toks) < 2 else safe_int(toks[1]) or 0
    threads = awoo.get_threads(sel.board, page)

    if threads:
        thr_fmt = threads_format(sel, page, threads)
        less(thr_fmt)
    else:
        print 'No threads on page %d.' % page

def cmd_get_replies(sel, toks):
    """\
    Fetches the replies in a particular thread.

    Usage: gr|get_replies [awoo thread]"""

    id = None
    replies = None

    try:
        id = int(toks[1])
    except IndexError:
        print 'No thread id specified.'
        return
    except ValueError:
        print 'Invalid thread id "%s".' % toks[1]
        return

    replies = awoo.get_thread_replies(id)

    if not replies:
        print 'Invalid thread id "%d".' % id
    else:
        thr_fmt = replies_format(replies)
        less(thr_fmt)

def cmd_selected(sel, _):
    """\
    Lists the selected board.

    Usage: sel|pwd"""

    print 'Browsing "%s".' % sel.board

def cmd_cd(sel, toks):
    """\
    Changes the currently selected board.

    Usage: cd|cb
           cd|cb [awoo board]"""

    if len(toks) < 2:
        if sel.board == sel.default:
            print 'Already browsing "%s".' % sel.default
            return
        else:
            sel.cd()
            print 'Now browsing "%s".' % sel.default
            return

    try:
        if sel.board == toks[1]:
            print 'Already browsing "%s".' % toks[1]
        else:
            sel.cd(toks[1])
            print 'Now browsing "%s".' % toks[1]
    except awoo.AwooException:
        print "Board \"%s\" doesn't exist." % toks[1]

def cmd_send_reply(sel, toks):
    """\
    Replies to a thread, given a thread id.

    Usage: re|reply [awoo thread]"""

    id = None

    try:
        id = int(toks[1])
    except IndexError:
        print 'No thread id specified.'
        return
    except ValueError:
        print 'Invalid thread id "%s".' % toks[1]
        return

    valid_thread = awoo.thread_exists(id)

    if not valid_thread:
        print 'Invalid thread id "%d".' % id
    else:
        reply = edit_(TMP('reply_body_%d' % id))

        if reply:
            try:
                awoo.post_reply(sel.board, id, reply)
                print 'Successfully replied to %d.' % id
            except awoo.AwooException as e:
                print e.message
        else:
            print 'Empty body, not posting reply.'

def cmd_blankpost(sel, toks):
    """\
    Sends a blank post to a specific thread.

    Usage: bp|blankpost|blankfag [awoo thread]"""

    id = None

    try:
        id = int(toks[1])
    except IndexError:
        print 'No thread id specified.'
        return
    except ValueError:
        print 'Invalid thread id "%s".' % toks[1]
        return

    valid_thread = awoo.thread_exists(id)

    if not valid_thread:
        print 'Invalid thread id "%d".' % id
    else:
        try:
            awoo.post_reply(sel.board, id, '')
            print 'Successfully sent blankpost to %d.' % id
        except awoo.AwooException as e:
            print e.message

def cmd_new_thread(sel, toks):
    """\
    Starts a new thread.

    Usage: nt|new_thread"""

    if sel.board == sel.default:
        print 'Please chooose a different board, "%s" is selected.' % sel.default
        return

    title = edit_(TMP('thread_title_%s' % sel.board))

    if not title:
        print 'Empty title, not posting new thread.'
        return

    reply = edit_(TMP('thread_body_%s' % sel.board))

    if not reply:
        print 'Empty body, not posting new thread.'
        return

    try:
        thr = awoo.new_thread(sel.board, title, reply)
        print 'Successfully started %s.' % thr
    except awoo.AwooException as e:
        print e.message

def cmd_search(sel, toks):
    """\
    Searches for a string of text in a board.

    Usage: search|find [board] [search string]"""

    ts = toks[2:]

    if len(toks) < 2:
        print 'No board or search string given.'
        return
    elif not ts:
        print 'Empty search string, not performing query.'
        return
    elif toks[1] not in awoo.get_boards():
        print "Board \"%s\" doesn't exist." % toks[1]
        return

    query = re_compile(' '.join(ts).lower(), re_M)

    page = 0
    threads = awoo.get_threads(toks[1], page)

    while threads:
        try:
            print 'Searching page %s.' % colors.red(str(page))

            _threads = None

            if toks[1] == sel.default and BOARD_BLACKLIST:
                _threads = [thr for thr in threads if 'title' in thr and thr['board'] not in BOARD_BLACKLIST]
            else:
                _threads = [thr for thr in threads if 'title' in thr]

            for thr in _threads:
                print '  ', colors.green('>'), 'Searching thread %s.' % colors.magenta('/%s/%d' % (toks[1], thr['post_id']))

                replies = awoo.get_thread_replies(thr['post_id'])

                if replies:
                    comment = replies[0]['title'].lower()
                    m = query.search(comment)

                    if m:
                        found = comment[m.start():41].replace('\r', '').replace('\n', ' ')
                        fmt = colors.white('(...%s...)' % found, style='faint')
                        id = colors.green(str(replies[0]['post_id']))
                        print '    ', colors.cyan('|'), 'Found in title %s %s.' % (id, fmt)
                        del m

                    for r in replies:
                        comment = r['comment'].lower()
                        m = query.search(comment)

                        if m:
                            found = comment[m.start():41].replace('\r', '').replace('\n', ' ')
                            fmt = colors.white('(...%s...)' % found, style='faint')
                            id = colors.green(str(r['post_id']))
                            print '    ', colors.cyan('|'), 'Found in reply %s %s.' % (id, fmt)
                            del m

            page += 1
            threads = awoo.get_threads(toks[1], page)
        except KeyboardInterrupt:
            print 'Search interrupted.'
            break

def cmd_pin_thread(_, toks):
    """\
    Saves a thread to read it later on another occasion.

    Usage: pin [awoo thread] [description]"""

    if len(toks) < 3:
        print 'No thread or description given.'
        return

    id = None
    ts = toks[2:]

    try:
        id = int(toks[1])
    except ValueError:
        print 'Invalid thread id "%s".' % toks[1]
        return

    if id in [x for (x, _) in DB]:
        print 'Thread "%d" is already in database.' % id
        return

    valid_thread = awoo.thread_exists(id)

    if not valid_thread:
        print 'Invalid thread id "%d".' % id
        return

    desc = ' '.join(ts)

    write_new_thr_database(id, desc)
    print 'Successfully saved thread "%d" in database.' % id

def cmd_unpin_thread(_, toks):
    """\
    Removes a thread from the pinned thread list.

    Usage: unpin [awoo thread]"""

    if not DB:
        print 'No threads in pinned list.'
        return

    if len(toks) < 2:
        print 'No thread given.'
        return

    id = None

    try:
        id = int(toks[1])
    except ValueError:
        if toks[1] == 'all':
            remove_all_thr_database()
            print 'Successfully removed all threads from pinned list.'
            return
        else:
            print 'Invalid thread id "%s".' % toks[1]
            return

    if id not in [_id for _id, _ in DB]:
        print "Can't find \"%d\" in pinned list." % id
        return

    remove_thr_database(id)
    print 'Successfully removed thread "%d" from pinned list.' % id

def cmd_pinned(_, _0):
    """\
    Returns the list of pinned threads.

    Usage: pinned"""

    if not DB:
        print 'No threads in pinned list.'
        return

    fmt = ''

    for thr in DB:
        fmt += '%d:\n    %s\n\n' % thr

    less(fmt)

def cmd_last_cmd(sel, _):
    """\
    Executes the last command again.

    Usage: r|repeat|!!"""

    if not sel.last_cmd:
        print 'No last command successfully executed in history.'
        return

    print ' '.join(sel.last_cmd)
    eval_cmd(sel, sel.last_cmd)

def cmd_blacklist(_, _0):
    """\
    Lists the blacklisted boards.

    Usage: blacklist"""

    if BOARD_BLACKLIST:
        for board in BOARD_BLACKLIST:
            stdout.write('%s  ' % board)

        stdout.write('\n')
    else:
        print 'Board blacklist is empty.'

def cmd_filter(sel, toks):
    """\
    Temporarily filters a board.

    Usage: filter [awoo board]
           filter all"""

    if len(toks) < 2:
        print 'No board to filter.'
        return

    global BOARD_BLACKLIST

    if toks[1] == 'all':
        BOARD_BLACKLIST = awoo.get_boards()
        print 'Filtered all boards.'
        return

    if toks[1] in BOARD_BLACKLIST:
        print 'Board "%s" is already being filtered.' % toks[1]
        return

    if toks[1] in awoo.get_boards():
        BOARD_BLACKLIST.append(toks[1])
        print 'Added "%s" to board blacklist.' % toks[1]
    else:
        print "Board \"%s\" doesn't exist." % toks[1]

def cmd_unfilter(_, toks):
    """\
    Removes a board from the blacklist.

    Usage: unfilter [awoo board]
           unfilter all"""

    if len(toks) < 2:
        print 'No board to unfilter.'
        return

    global BOARD_BLACKLIST

    if toks[1] == 'all':
        del BOARD_BLACKLIST[:]
        print 'Cleared the blacklist.'
        return

    try:
        BOARD_BLACKLIST.remove(toks[1])
        print 'Removed "%s" from the blacklist.' % toks[1]
    except ValueError:
        print "Can't find \"%s\" in the blacklist." % toks[1]

# dictionary contains the appropriate functions
# to call upon a certain command being read
CMD_DICT = {
    'h': cmd_help,
    'help': cmd_help,
    'cls': cmd_clear,
    'clear': cmd_clear,
    'q': cmd_quit,
    'quit': cmd_quit,
    'exit': cmd_quit,
    'ls': cmd_get_boards,
    'gb': cmd_get_boards,
    'get_boards': cmd_get_boards,
    'gr': cmd_get_replies,
    'get_replies': cmd_get_replies,
    'gt': cmd_get_threads,
    'get_threads': cmd_get_threads,
    'cd': cmd_cd,
    'cb': cmd_cd,
    'sel': cmd_selected,
    'pwd': cmd_selected,
    're': cmd_send_reply,
    'reply': cmd_send_reply,
    'bp': cmd_blankpost,
    'blankfag': cmd_blankpost,
    'blankpost': cmd_blankpost,
    'nt': cmd_new_thread,
    'new_thread': cmd_new_thread,
    'pin': cmd_pin_thread,
    'unpin': cmd_unpin_thread,
    'pinned': cmd_pinned,
    'search': cmd_search,
    'find': cmd_search,
    '!!': cmd_last_cmd,
    'r': cmd_last_cmd,
    'repeat': cmd_last_cmd,
    'blacklist': cmd_blacklist,
    'filter': cmd_filter,
    'unfilter': cmd_unfilter,
}

def main():
    try:
        sel = CurrentBoard()
    except awoo.AwooException:
        print '%s:%d is down.' % (awoo.conn.cfg['host'], awoo.conn.cfg['port'])
        exit(1)

    while True:
        try:
            # print prompt
            stdout.write('%s ' % PROMPT)

            # read line from stdin
            line = stdin.readline()

            if not line:
                # exit on 'EOF'
                stdout.write('\n')
                exit(0)
            else:
                # strip the newline character
                line = line.strip()

            # eval commands read
            toks = line.decode('utf-8').split(' ')
            eval_cmd(sel, toks)
        except (IOError, KeyboardInterrupt):
            stdout.write('\n')
            continue

if __name__ == '__main__':
    main()
