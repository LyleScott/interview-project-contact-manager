DEBUG_MODE = True

DB_URI = 'mysql://root:fament@localhost/contactmanager'
DB_URI_ARGS = {}
if DEBUG_MODE is True:
    DB_URI_ARGS.update({'echo': True})
