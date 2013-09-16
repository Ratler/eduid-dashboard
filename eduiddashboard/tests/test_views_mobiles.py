import json

from mock import patch

from eduiddashboard.testing import LoggedInReguestTests
from eduiddashboard.userdb import UserDB


class MailsFormTests(LoggedInReguestTests):

    formname = 'mobilesview-form'

    def test_logged_get(self):
        self.set_logged()
        response = self.testapp.get('/profile/mobiles/')

        self.assertEqual(response.status, '200 OK')
        self.assertIsNotNone(getattr(response, 'form', None))

    def test_notlogged_get(self):
        response = self.testapp.get('/profile/mobiles/')
        self.assertEqual(response.status, '302 Found')

    def test_add_valid_mobile(self):
        self.set_logged()

        response_form = self.testapp.get('/profile/mobiles/')

        form = response_form.forms[self.formname]

        form['mobile'].value = '+34678455654'
        with patch.object(UserDB, 'exists_by_field', clear=True):
            UserDB.exists_by_field.return_value = False

            response = form.submit('add')

            self.assertEqual(response.status, '200 OK')
            self.assertIn('+34678455654', response.body)
            self.assertIsNotNone(getattr(response, 'form', None))

    def test_add_not_valid_mobile(self):
        self.set_logged()

        response_form = self.testapp.get('/profile/mobiles/')

        form = response_form.forms[self.formname]

        for bad_value in ('not_a_number', '545455'):
            form['mobile'].value = bad_value
            with patch.object(UserDB, 'exists_by_field', clear=True):
                UserDB.exists_by_field.return_value = False
                response = form.submit('add')

                self.assertEqual(response.status, '200 OK')
                self.assertIn('alert-error', response.body)
                self.assertIn('Invalid telephone number', response.body)
                self.assertIsNotNone(getattr(response, 'form', None))

    def test_remove_existant_mobile(self):
        self.set_logged()
        userdb = self.db.profiles.find({'_id': self.user['_id']})[0]
        mobiles_number = len(userdb['mobile'])

        response = self.testapp.post(
            '/profile/mobiles-actions/',
            {'identifier': 0, 'action': 'remove'}
        )
        userdb_after = self.db.profiles.find({'_id': self.user['_id']})[0]
        response_json = json.loads(response.body)
        self.assertEqual(response_json['result'], 'ok')
        self.assertEqual(mobiles_number - 1, len(userdb_after['mobile']))

    def test_remove_not_existant_mobile(self):
        self.set_logged()
        userdb = self.db.profiles.find({'_id': self.user['_id']})[0]
        mobiles_number = len(userdb['mobile'])

        with self.assertRaises(IndexError):
            self.testapp.post(
                '/profile/mobiles-actions/',
                {'identifier': 10, 'action': 'remove'}
            )
        userdb_after = self.db.profiles.find({'_id': self.user['_id']})[0]
        self.assertEqual(mobiles_number, len(userdb_after['mobile']))
