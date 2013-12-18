"""Webapp2 interface to the Contact Manger webapp."""

import os
import mimetypes

from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm import sessionmaker

import webapp2
import ujson

from src import constants
from src import common
from src import models


class BaseHandler(webapp2.RequestHandler):
    """A handler that allows for attaching a db_session to a handler."""

    def __init__(self, *args, **kwargs):
        """Initialize with a specific engine."""
        super(BaseHandler, self).__init__(*args, **kwargs)
        if hasattr(self.app, 'engine'):
            self.engine = self.app.engine
        else:
            self.engine = models.get_engine()

    def dispatch(self):
        """Add the database session to the request's scope."""
        try:
            self.db_session = scoped_session(sessionmaker(bind=self.engine))
            ret = super(BaseHandler, self).dispatch()
            self.db_session.commit()
            return ret
        except:
            self.db_session.rollback()
            raise


class Index(BaseHandler):
    """The index page that the user lands on when they hit this app."""

    def get(self):
        """Serve up the index template that will load the JS frontend."""
        template_vals = {}

        contactmgrs = self.db_session.query(models.ContactManager).all()
        if contactmgrs and contactmgrs[0].contacts:
            contactmgrs = contactmgrs[0]
            template_vals.update(
                {'existing_contacts': contactmgrs.to_table_row_html()})
        else:
            template_vals.update({'existing_contacts': '<tbody></tbody>'})

        template = common.JINJA_ENV.get_template('templates/index.html')
        self.response.out.write(template.render(template_vals))


class ContactManager(BaseHandler):
    """The CRUD controller for contact manager actions."""

    def post(self):
        """Create new contact entries."""
        # TODO: tie a contactmgr to User?
        mgrs = self.db_session.query(models.ContactManager).all()
        if mgrs:
            contactmgr = mgrs[0]
        else:
            contactmgr = models.ContactManager()
            self.db_session.add(contactmgr)

        status = contactmgr.update_from_post(self.request, self.db_session)
        if status is None:
            # TODO: This should be handled in the frontend with ui-state-error.
            return False

        self.db_session.add(contactmgr)

        if contactmgr.id < 1:
            self.db_session.commit()

        self.response.out.write(ujson.dumps(status))

    def delete(self):
        """Delete contact entries."""
        try:
            ids = map(int, ujson.loads(self.request.body))
        except:
            if constants.DEBUG_MODE is True:
                raise
            return

        if ids == []:
            return

        contacts = self.db_session.query(models.Contact
            ).filter(models.Contact.id.in_(ids)).all()

        map(self.db_session.delete, contacts)

        self.response.out.write(True);


class StaticFileHandler(webapp2.RequestHandler):
    """Handle static files in paste."""

    def get(self, path):
        """Serve up a file corresponding to a GET request."""
        abs_path = os.path.abspath(os.path.join(
            self.app.config.get('webapp2_static.static_file_path', 'static'),
            path))
        if os.path.isdir(abs_path) or abs_path.find(os.getcwd()) != 0:
            self.response.set_status(403)
            return
        try:
            f = open(abs_path, 'r')
            self.response.headers['Content-Type'] = mimetypes.guess_type(
                abs_path)[0]
            self.response.out.write(f.read())
            f.close()
        except:
            self.response.set_status(404)


APP = webapp2.WSGIApplication([
    ('/', Index),
    ('/cmgr', ContactManager),
    (r'/static/(.+)', StaticFileHandler)
], debug=True)


def main():
    from paste import httpserver
    httpserver.serve(APP, host='127.0.0.1', port='8080')
    #APP.run()


if __name__ == '__main__':
    main()
