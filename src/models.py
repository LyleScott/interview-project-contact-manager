"""Model declarations to serialize into a database structures and structures
that the front end will understand.
"""

from datetime import datetime

import ujson
from sqlalchemy import Column, DateTime, Integer, ForeignKey, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.orm.scoping import scoped_session

from src import constants


def get_engine():
    """Get the engine as specified by the constant configuration."""
    return create_engine(constants.DB_URI, **constants.DB_URI_ARGS)


#Session = scoped_session(sessionmaker(bind=get_engine()))
Base = declarative_base()


class BaseMixIn(object):
    """A MixIn to easily add in needed metadata in all tables."""
    #Base.query = Session.query_property()
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.utcnow())
    modified = Column(
        DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())


class Contact(Base, BaseMixIn):
    """A contact container that has a parent of a ContactList and holds
    the basic name information and a relation to the address.
    """
    __tablename__ = 'contacts'

    contactmgr_id = Column(Integer, ForeignKey('contactmgrs.id'))
    firstname = Column(String(128))
    lastname = Column(String(128))
    zipcode = Column(String(16))
    city = Column(String(256))
    state = Column(String(4))

    def __init__(self, firstname='', lastname='', zipcode='', city='',
                 state=''):
        """Initialize instance."""
        self.firstname = firstname
        self.lastname = lastname
        self.zipcode = zipcode
        self.city = city
        self.state = state

    def __repr__(self):
        """Human readable representation."""
        fmt = '<%s(id=%s, cmgrId=%s, firstname=%s, lastname=%s) %s>'
        return fmt % (self.__class__.__name__, self.id, self.contactmgr_id,
                      self.firstname, self.lastname, hex(id(self)))

    def to_dict(self):
        """Serialize to a dict."""
        return {
            'id': self.id,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'zipcode': self.zipcode,
            'city': self.city,
            'state': self.state,
        }


class ContactManager(Base, BaseMixIn):
    """A contact manager is responsible for contact relations."""
    __tablename__ = 'contactmgrs'

    title = Column(String(256))
    contacts = relationship('Contact', backref='contactmgrs')

    def __init__(self, title='', contacts=None):
        """Initialize instance."""
        self.title = title
        self.contacts = contacts or []

    def __repr__(self):
        """Human readable representation."""
        contact_ids = [contact.id for contact in self.contacts or []]
        fmt = '<%s(id=%s, title=%s, contactIds=%s) %s>'
        return fmt % (self.__class__.__name__, self.id, self.title,
                      contact_ids, hex(id(self)))

    def to_dict(self):
        """Serialize to a dict."""
        contacts = [contact.to_dict() for contact in self.contacts or []]
        return {
            'id': self.id,
            'title': self.title,
            'contacts': contacts,
        }

    def to_table_row_html(self):
        """Serialize the existing contacts to initialize the existing contacts
        table.
        """
        rows = []

        delete_check = ('<td class="delcol"><input type="checkbox" ' +
                        'name="delete" id="delete"></td>')
        id_fmt = '<td class="idcol">%s</td>'
        data_fmt_rw = '<td class="edit %s">%s</td>'
        data_fmt_ro = '<td class="%s">%s</td>'

        for contact in self.contacts:
            contact_dict = contact.to_dict()
            row = [
                delete_check,
                id_fmt % contact_dict['id'],
                data_fmt_rw % ('firstname', contact_dict['firstname']),
                data_fmt_rw % ('lastname', contact_dict['lastname']),
                data_fmt_rw % ('zipcode', contact_dict['zipcode']),
                data_fmt_ro % ('city', contact_dict['city']),
                data_fmt_ro % ('state', contact_dict['state']),
            ]
            rows.append('<tr>%s</tr>' % ''.join(row))

        return ''.join(rows)

    def update_from_post(self, request, session):
        """Serialize a POST request into either creating new contacts or
        updating existing contacts.
        """
        try:
            existing = [contact.id for contact in self.contacts]
            modified = []

            rows = ujson.loads(request.body)
            for _, id_, fname, lname, zipcode, city, state in rows:
                if id_ == '-1':
                    contact = Contact(
                        fname, lname, zipcode, city, state)
                    self.contacts.append(contact)
                else:
                    contact = filter(lambda x: x.id == int(id_), self.contacts)
                    if not contact:
                        if constants.DEBUG_MODE is True:
                            raise Exception(
                                'Updating contact %s, but it doesn\t exist!' %
                                id_)
                        else:
                            # TODO: This needs to be handled properly on the
                            # frontend.
                            continue
                    else:
                        contact = contact[0]

                    # TODO: what would need to happen here is some nice way to
                    # compare values to either say "hey, this changed" and
                    # update all values. A better way would be to obviously
                    # build a batch of partial updates and batch them.
                    #
                    # For simplicity, i'll just update the contact regardless.

                    contact.firstname = fname
                    contact.lastname = lname
                    contact.zipcode = zipcode
                    contact.city = city
                    contact.state = state

                    session.add(contact)

                    modified.append(contact.id)

            # Establish ids for the contacts.
            session.commit()

            # Get the ids of the new contacts.
            current = [contact.id for contact in self.contacts]
            created = set(current) - set(existing)
        except:
            if constants.DEBUG_MODE is True:
                raise

        return {'created': created, 'modified': modified}


def init_model(engine=None):
    """Serialize the models into database tables."""
    Base.metadata.create_all(engine or get_engine())


if __name__ == '__main__':
    init_model()
