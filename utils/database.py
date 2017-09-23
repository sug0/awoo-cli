import gzip
import cPickle as pickle

from io import BytesIO

# load db to memory
def load(db_path):
    db = None

    try:
        with gzip.open(db_path, 'rb') as gz:
            bytes = gz.read()
            db = pickle.loads(bytes)
            gz.close()

        return db
    except IOError:
        return None

# write db from memory to disk
def write(db, db_path):
    with BytesIO() as writer:
        with gzip.open(db_path, 'wb') as gz:
            pickle.dump(db, writer)
            gz.write(writer.getvalue())
            writer.close()
            gz.close()
