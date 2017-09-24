import awoo

def sep_chunks(f, size=500):
    chunks = []

    chnk = f.read(size)

    while chnk:
        chunks.append(chnk)
        chnk = f.read(size)

    return chunks

def main(argv):
    if len(argv) < 4:
        print 'Usage: python %s [awoo board] [awoo thread] [file]' % argv[0]
        exit(1)

    try:
        with open(argv[3], 'r') as f:
            chunks = sep_chunks(f)
            board = argv[1]
            thread = int(argv[2])

            i = 1
            sz = len(chunks)

            print 'Chunks to post: %d' % sz

            for chunk in chunks:
                print 'Posting %d/%d chunks...' % (i, sz)
                awoo.post_reply(board, thread, chunk)
                i += 1
                sleep(5)

            f.close()
    except awoo.AwooException as e:
        print e.message
        exit(2)
    except ValueError:
        print 'Invalid thread "%s".' % argv[2]
        exit(3)
    except IOError:
        print 'Invalid file "%s".' % argv[3]
        exit(4)

    print 'Successfully posted to thread /%s/%d.' % (board, thread)

if __name__ == '__main__':
    from time import sleep
    from sys import argv, exit

    main(argv)
