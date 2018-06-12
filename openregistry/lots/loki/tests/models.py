# -*- coding: utf-8 -*-
import unittest
import mock

from datetime import timedelta

from schematics.exceptions import ModelValidationError

from openregistry.lots.core.utils import get_now

from openregistry.lots.loki.models import (
    StartDateRequiredPeriod,
    BankAccount,
    Auction,
)

now = get_now()


class DummyModelsTest(unittest.TestCase):

    def test_StartDateRequiredPeriod(self):
        period = StartDateRequiredPeriod()

        self.assertEqual(period.serialize(), None)
        with self.assertRaisesRegexp(ValueError, 'Period Model has no role "test"'):
            period.serialize('test')
        with self.assertRaisesRegexp(ModelValidationError, u'This field is required.'):
            period.validate()
        data = {'startDate': now.isoformat()}
        period.import_data(data)
        period.validate()
        self.assertEqual(period.serialize(), data)
        data['endDate'] = now.isoformat()
        period.import_data(data)
        period.validate()
        self.assertEqual(period.serialize(), data)
        period.startDate += timedelta(3)
        with self.assertRaises(ModelValidationError) as ex:
            period.validate()
        self.assertEqual(ex.exception.messages,
                         {"startDate": ["period should begin before its end"]})

    def test_BankAccount(self):
        data = {
            'name': 'Name'
        }

        account_details = BankAccount()
        self.assertEqual(account_details.serialize(), None)
        with self.assertRaisesRegexp(ValueError, 'BankAccount Model has no role "test"'):
            account_details.serialize('test')

        account_details.import_data(data)
        with self.assertRaises(ModelValidationError) as ex:
            account_details.validate()
        self.assertEqual(
            ex.exception.messages,
            {
                'accountIdentification': [u'Please provide at least 1 item.'],
                'bankName': [u'This field is required.']
            }
        )

        data['accountIdentification'] = [
            {
                'scheme': 'wrong',
                'id': '1231232'
            }
        ]
        data['bankName'] = 'bankName'
        account_details.import_data(data)
        with self.assertRaises(ModelValidationError) as ex:
            account_details.validate()
        self.assertEqual(
            ex.exception.messages,
            {'accountIdentification': [{
                 'scheme': [u"Value must be one of ['UA-EDR', 'UA-MFO', 'accountNumber']."],
                 'description': [u"This field is required."]
                }]
            }
        )

        data['accountIdentification'] = [
            {
                'scheme': 'UA-MFO',
                'id': '1231232',
                'description': 'just description'
            }
        ]
        account_details.import_data(data)
        account_details.validate()

    def test_Auction(self):
        data = {
            "procurementMethodType": "sellout.english",
            "auctionPeriod": {
                "startDate": now.isoformat(),
                "endDate": (now + timedelta(days=5)).isoformat()
            },
            "tenderAttempts": 3,
            "tenderingDuration": 'P4DT5H',
            "guarantee": {
                "amount": 30.54,
                "currency": "UAH"
            },
            "minimalStep": {
                "amount": 60.54,
                "currency": "UAH"
            },
            "value": {
                "amount": 1500.54,
                "currency": "UAH"
            },
            "auctionParameters": {
                "type": "insider",
            }
        }
        auction = Auction()
        auction.import_data(data)
        auction.validate()

        data['auctionParameters'] = {'dutchSteps': 0, 'type': 'insider'}
        auction.import_data(data)
        with self.assertRaises(ModelValidationError) as ex:
            auction.validate()
        self.assertEqual(
            ex.exception.messages,
            {'auctionParameters':
                 {'dutchSteps': [u'Int value should be greater than 1.']}
            }
        )

        data['auctionParameters'] = {'dutchSteps': 100, 'type': 'insider'}
        auction.import_data(data)
        with self.assertRaises(ModelValidationError) as ex:
            auction.validate()
        self.assertEqual(
            ex.exception.messages,
            {'auctionParameters':
                 {'dutchSteps': [u'Int value should be less than 99.']}
            }
        )

        auction = Auction()
        data['auctionParameters'] = {'dutchSteps': 55, 'type': 'insider'}
        data['procurementMethodType'] = 'sellout.insider'
        auction.import_data(data)
        auction.validate()
        self.assertEqual(auction.auctionParameters.dutchSteps, data['auctionParameters']['dutchSteps'])

        data['relatedProcessID'] = 'relatedProcessID'
        data['auctionID'] = 'auctionID'

        auction.import_data(data)

        edit_serialization = auction.serialize('edit')
        self.assertNotIn('relatedProcessID', edit_serialization)
        self.assertNotIn('auctionID', edit_serialization)

        edit_serialization = auction.serialize('create')
        self.assertNotIn('relatedProcessID', edit_serialization)
        self.assertNotIn('auctionID', edit_serialization)


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(DummyModelsTest))
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
