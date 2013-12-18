"""Test suite for models.py to confirm that the model schema supports the
relationships and attributes vital to functionality.
"""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import ujson
import webapp2

from src import contact_manager
from src import models


class CommonFixture(unittest.TestCase):
    """Common fixtures used in the tests."""

    def setUp(self):
        """Initialize a fresh in-memory DB."""
        engine = create_engine('sqlite:///:memory:', echo=True)
        self.session = sessionmaker(bind=engine)()
        models.init_model(engine)
        contact_manager.APP.engine = engine

    def tearDown(self):
        """Clobber the session."""


class TestContact(CommonFixture):
    """Test aspects of the Contact model."""

    def setUp(self):
        """Initialize test fixture."""
        super(TestContact, self).setUp()
        self.contact = models.Contact(
            'foo', 'bar', 'zipcode', 'city', 'state')
        self.session.add(self.contact)
        self.session.commit()

    def test__repr__(self):
        """Assert that __repr__ spits out the correct format."""
        self.assertEqual(
            ('<Contact(id=%s, cmgrId=None, firstname=foo, lastname=bar'
             ') %s>') % (self.contact.id, hex(id(self.contact))),
            str(self.contact))

    def test_to_dict(self):
        """Assert that the json serialization is correct."""
        json = self.contact.to_dict()
        expected = {
            'id': self.contact.id,
            'firstname': 'foo',
            'lastname': 'bar',
            'zipcode': 'zipcode',
            'city': 'city',
            'state': 'state',
        }
        self.assertEqual(json, expected)


class TestContactManager(CommonFixture):
    """"Test aspects of the ContactManager model."""

    def setUp(self):
        """Initialize test fixture."""
        super(TestContactManager, self).setUp()
        self.contact1 = models.Contact(
            'first1', 'last1', 'zip1', 'city1', 'state1')
        self.contact2 = models.Contact(
            'first2', 'last2', 'zip2', 'city2', 'state2')
        self.contactmgr = models.ContactManager(
            'title', contacts=[self.contact1, self.contact2])
        self.session.add(self.contactmgr)
        self.session.commit()

    def test__repr__(self):
        """Assert that __repr__ spits out the correct format."""
        self.assertEqual(
            '<ContactManager(id=%s, title=title, contactIds=%s) %s>' %
            (self.contactmgr.id, [self.contact1.id, self.contact2.id],
             hex(id(self.contactmgr))),
            str(self.contactmgr))

    def test_to_dict(self):
        """Assert that the json serialization is correct."""
        json = self.contactmgr.to_dict()
        expected = {
            'id': self.contactmgr.id,
            'title': 'title',
            'contacts': [{
                'id': self.contact1.id,
                'firstname': 'first1',
                'lastname': 'last1',
                'zipcode': 'zip1',
                'city': 'city1',
                'state': 'state1',
                }, {
                'id': self.contact2.id,
                'firstname': 'first2',
                'lastname': 'last2',
                'zipcode': 'zip2',
                'city': 'city2',
                'state': 'state2',
                }]
        }
        self.assertEqual(json, expected)

    def test_to_table_row_html(self):
        """Test that a ContactManager instance can be serialized into
        table rows to easily initialize a contact table.
        """
        html = self.contactmgr.to_table_row_html()
        expected = (
            '<tr><td class="delcol"><input type="checkbox" name="' +
            'delete" id="delete"></td><td class="idcol">1</td><td class="edi' +
            't firstname">first1</td><td class="edit lastname">last1</td><td' +
            ' class="edit zipcode">zip1</td><td class="city">city1</td><td' +
            ' class="state">state1</td></tr><tr><td class="delcol"><input ' +
            'type="checkbox" name="delete" id="delete"></td><td class=' +
            '"idcol">2</td><td class="edit firstname">first2</td><td class=' +
            '"edit lastname">last2</td><td class="edit zipcode">zip2</td><td' +
            ' class="city">city2</td><td class="state">state2</td></tr>')
        self.assertEqual(html, expected)

    def test_update_from_post__1_new_contact(self):
        """Assert that adding a contact in a POSTed form results in the
        correct info on the contact manager instance.
        """
        request = webapp2.Request.blank('/')
        request.body = ujson.dumps([
            ['', '-1', 'f1', 'l1', 'z1', 'c1', 's1'],
        ])

        contactmgr = models.ContactManager()
        contactmgr.update_from_post(request, self.session)

        self.assertEquals(len(contactmgr.contacts), 1)

        contact = contactmgr.contacts[0]

        self.assertEqual(contact.firstname, 'f1')
        self.assertEqual(contact.lastname, 'l1')
        self.assertEqual(contact.zipcode, 'z1')
        self.assertEqual(contact.city, 'c1')
        self.assertEqual(contact.state, 's1')

    def test_update_from_post__N_new_contact(self):
        """Assert that adding a contact in a POSTed form results in the
        correct info on the contact manager instance.
        """
        request = webapp2.Request.blank('/')
        request.body = ujson.dumps([
            ['', '-1', 'f1', 'l1', 'z1', 'c1', 's1'],
            ['', '-1', 'f2', 'l2', 'z2', 'c2', 's2'],
        ])

        contactmgr = models.ContactManager()
        contactmgr.update_from_post(request, self.session)

        self.assertEquals(len(contactmgr.contacts), 2)

        contact = contactmgr.contacts[0]
        self.assertEqual(contact.firstname, 'f1')
        self.assertEqual(contact.lastname, 'l1')
        self.assertEqual(contact.zipcode, 'z1')
        self.assertEqual(contact.city, 'c1')
        self.assertEqual(contact.state, 's1')

        contact = contactmgr.contacts[1]
        self.assertEqual(contact.firstname, 'f2')
        self.assertEqual(contact.lastname, 'l2')
        self.assertEqual(contact.zipcode, 'z2')
        self.assertEqual(contact.city, 'c2')
        self.assertEqual(contact.state, 's2')

    def test_update_from_post__1_edit_contact(self):
        """Assert that adding a contact in a POSTed form results in the
        correct info on the contact manager instance.
        """
        request = webapp2.Request.blank('/')
        request.body = ujson.dumps([
            ['', self.contact1.id, 'f1', 'l1', 'z1', 'c1', 's1'],
        ])

        contactmgr = models.ContactManager(contacts=[self.contact1])
        contactmgr.update_from_post(request, self.session)

        self.assertEquals(len(contactmgr.contacts), 1)

        contact = contactmgr.contacts[0]
        self.assertEqual(contact.id, self.contact1.id)
        self.assertEqual(contact.firstname, 'f1')
        self.assertEqual(contact.lastname, 'l1')
        self.assertEqual(contact.zipcode, 'z1')
        self.assertEqual(contact.city, 'c1')
        self.assertEqual(contact.state, 's1')

    def test_update_from_post__N_edit_contact(self):
        """Assert that adding a contact in a POSTed form results in the
        correct info on the contact manager instance.
        """
        request = webapp2.Request.blank('/')
        request.body = ujson.dumps([
            ['', self.contact1.id, 'f1', 'l1', 'z1', 'c1', 's1'],
            ['', self.contact2.id, 'f2', 'l2', 'z2', 'c2', 's2'],
        ])

        contactmgr = models.ContactManager(
            contacts=[self.contact1, self.contact2])
        contactmgr.update_from_post(request, self.session)

        self.assertEquals(len(contactmgr.contacts), 2)

        contact = contactmgr.contacts[0]
        self.assertEqual(contact.id, self.contact1.id)
        self.assertEqual(contact.firstname, 'f1')
        self.assertEqual(contact.lastname, 'l1')
        self.assertEqual(contact.zipcode, 'z1')
        self.assertEqual(contact.city, 'c1')
        self.assertEqual(contact.state, 's1')

        contact = contactmgr.contacts[1]
        self.assertEqual(contact.id, self.contact2.id)
        self.assertEqual(contact.firstname, 'f2')
        self.assertEqual(contact.lastname, 'l2')
        self.assertEqual(contact.zipcode, 'z2')
        self.assertEqual(contact.city, 'c2')
        self.assertEqual(contact.state, 's2')

    def test_update_from_post__1_create_1_edit_contact(self):
        """Assert that adding a contact in a POSTed form results in the
        correct info on the contact manager instance.
        """
        request = webapp2.Request.blank('/')
        request.body = ujson.dumps([
            ['', self.contact1.id, 'f1', 'l1', 'z1', 'c1', 's1'],
            ['', '-1', 'f2', 'l2', 'z2', 'c2', 's2'],
        ])

        contactmgr = models.ContactManager(contacts=[self.contact1])
        contactmgr.update_from_post(request, self.session)

        self.assertEquals(len(contactmgr.contacts), 2)

        contact = contactmgr.contacts[0]
        self.assertEqual(contact.id, self.contact1.id)
        self.assertEqual(contact.firstname, 'f1')
        self.assertEqual(contact.lastname, 'l1')
        self.assertEqual(contact.zipcode, 'z1')
        self.assertEqual(contact.city, 'c1')
        self.assertEqual(contact.state, 's1')

        contact = contactmgr.contacts[1]
        self.assertEqual(contact.firstname, 'f2')
        self.assertEqual(contact.lastname, 'l2')
        self.assertEqual(contact.zipcode, 'z2')
        self.assertEqual(contact.city, 'c2')
        self.assertEqual(contact.state, 's2')
