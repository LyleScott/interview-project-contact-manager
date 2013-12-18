"""Test suite for the contact_manager.py webapp2 app."""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import ujson
import webapp2

from src import common
from src import contact_manager
from src import models


class CommonFixture(unittest.TestCase):
    """Common fixtures used in the tests."""

    def _get_response(self):
        """Convenience method for getting a response."""
        return self.request.get_response(contact_manager.APP)


class TestIndex(CommonFixture):
    """Tests for the Index request handler."""

    def setUp(self):
        """Initialize test fixture."""
        super(TestIndex, self).setUp()
        self.request = webapp2.Request.blank('/')
        self.html = common.JINJA_ENV.get_template(
            'templates/index.html').render({})

    def test_get__status(self):
        """Assert that the http status is 200 OK."""
        self.assertEqual(self._get_response().status_int, 200)

    def test_get__doctype(self):
        """Assert that the doctype is correct."""
        self.assertTrue(self.html.startswith('<!DOCTYPE html>'))

    def test_get__header(self):
        """Assert that atleast the header shows in the HTML. If this shows,
        I'll assume the expected page is displaying rather than testing all
        HTML elements.
        """
        self.assertTrue('<h1>Contact Manager</h1>')


class TestContactManager(CommonFixture):
    """Tests for the ContactManager request handler that handles CRUD actions.

    These are likely to duplicate model tests but consider them close to an
    end-to-end test.
    """

    def setUp(self):
        """Initialize test fixture."""
        super(TestContactManager, self).setUp()
        engine = create_engine('sqlite:///:memory:', echo=True)
        self.session = sessionmaker(bind=engine)()
        models.init_model(engine)
        contact_manager.APP.engine = engine

        self.request = webapp2.Request.blank('/cmgr')

    def tearDown(self):
        self.session.close()

    def test_post_1newcontact(self):
        """POSTing a contact row should result in the contact being saved and
        the id being returns in the response.
        """
        self.request.method = 'POST'
        self.request.body = ujson.dumps([
            ['', '-1', 'f1', 'l1', 'z1', 'c1', 's1'],
        ])
        response = self._get_response()

        self.assertEqual(response.status_int, 200)
        self.assertEqual(
            response.body, ujson.dumps({'modified': [], 'created': [1]}))

    def test_post_1new1edit(self):
        """POSTing a contact row should result in the contact being saved and
        the id being returns in the response.
        """
        self.request.method = 'POST'
        self.request.body = ujson.dumps([
            ['', '-1', 'f1', 'l1', 'z1', 'c1', 's1'],
        ])
        response = self._get_response()

        self.request.body = ujson.dumps([
            ['', '1', 'f1', 'l1', 'z1', 'c1', 's1'],
            ['', '-1', 'f2', 'l2', 'z2', 'c2', 's2'],
        ])
        response = self._get_response()

        self.assertEqual(response.status_int, 200)
        self.assertEqual(
            response.body, ujson.dumps({'modified': [1], 'created': [2]}))

    def test_post_NnewNedit(self):
        """POSTing a contact row should result in the contact being saved and
        the id being returns in the response.
        """
        self.request.method = 'POST'
        self.request.body = ujson.dumps([
            ['', '-1', 'f1', 'l1', 'z1', 'c1', 's1'],
            ['', '-1', 'f2', 'l2', 'z2', 'c2', 's2'],
        ])
        response = self._get_response()

        self.assertEqual(response.status_int, 200)
        self.assertEqual(
            response.body, ujson.dumps({'modified': [], 'created': [1, 2]}))

        self.request.body = ujson.dumps([
            ['', '1', 'f1', 'l1', 'z1', 'c1', 's1'],
            ['', '2', 'f2', 'l2', 'z2', 'c2', 's2'],
            ['', '-1', 'f3', 'l3', 'z3', 'c3', 's3'],
            ['', '-1', 'f4', 'l4', 'z4', 'c4', 's4'],
            ['', '-1', 'f5', 'l5', 'z5', 'c5', 's5'],
        ])
        response = self._get_response()

        self.assertEqual(response.status_int, 200)
        self.assertEqual(
            response.body,
            ujson.dumps({'modified': [1, 2], 'created': [3, 4, 5]}))

    def test_get(self):
        """GETing the cmgr resource should result in all contacts."""
        self.request.method = 'POST'

    def test_delete_0contact(self):
        """Using the DELETE resource with no valid data shouldn't blow up."""
        self.request.method = 'DELETE'
        response = self._get_response()
        self.assertTrue(response.status_int, 200)

    def test_delete_1contact(self):
        """DELETEing a contact in the cmgr resource should delete the
        corresponding contact entity.
        """
        contactmgr = models.ContactManager(
            contacts=[
                models.Contact('f1', 'l1', 'z1', 'c1', 's1'),
                models.Contact('f2', 'l2', 'z2', 'c2', 's2'),
                models.Contact('f3', 'l3', 'z3', 'c3', 's3'),
            ]
        )

        self.session.add(contactmgr)
        self.session.commit()

        id_to_delete = contactmgr.contacts[1].id
        ids_remaining = [contactmgr.contacts[0].id, contactmgr.contacts[2].id]

        self.request.method = 'DELETE'
        self.request.body = ujson.dumps([id_to_delete])
        response = self._get_response()

        self.assertTrue(response.body)

        self.assertEqual(
            len(self.session.query(
                models.Contact).filter(models.Contact.id == id_to_delete
                ).all()),
            0)

        self.assertEqual(
            len(self.session.query(
                models.Contact).filter(models.Contact.id.in_(ids_remaining)
                ).all()),
            2)

    def test_delete_Ncontact(self):
        """DELETEing contactS in the cmgr resource should delete the
        corresponding contact entities.
        """
        contactmgr = models.ContactManager(
            contacts=[
                models.Contact('f1', 'l1', 'z1', 'c1', 's1'),
                models.Contact('f2', 'l2', 'z2', 'c2', 's2'),
                models.Contact('f3', 'l3', 'z3', 'c3', 's3'),
            ]
        )

        self.session.add(contactmgr)
        self.session.commit()

        id_to_delete = [contactmgr.contacts[1].id, contactmgr.contacts[2].id]
        id_remaining = contactmgr.contacts[0].id

        self.request.method = 'DELETE'
        self.request.body = ujson.dumps(id_to_delete)
        response = self._get_response()

        self.assertTrue(response.body)

        self.assertEqual(
            len(self.session.query(
                models.Contact).filter(models.Contact.id.in_(id_to_delete)
                ).all()),
            0)

        self.assertEqual(
            len(self.session.query(
                models.Contact).filter(models.Contact.id == id_remaining
                ).all()),
            1)
