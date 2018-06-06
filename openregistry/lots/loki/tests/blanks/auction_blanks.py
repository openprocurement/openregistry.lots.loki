# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy
from datetime import timedelta

from openregistry.lots.core.utils import (
    get_now,
    calculate_business_date
)
from openregistry.lots.core.models import Period
from openregistry.lots.loki.models import Lot
from openregistry.lots.core.constants import SANDBOX_MODE
from openregistry.lots.loki.constants import DEFAULT_DUTCH_STEPS, DEFAULT_REGISTRATION_FEE

from openregistry.lots.loki.tests.base import (
    create_single_lot,
    check_patch_status_200,
    add_decisions,
    add_auctions
)


def patch_auctions_with_lot(self):
    self.app.authorization = ('Basic', ('broker', ''))

    response = create_single_lot(self, self.initial_data)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    # Move from 'draft' to 'pending' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    add_auctions(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)


    self.app.authorization = ('Basic', ('concierge', ''))

    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification')
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending')

    self.app.authorization = ('Basic', ('broker', ''))


    data = deepcopy(lot)
    del data['decisions']
    del data['status']
    data['auctions'][0]['tenderAttempts'] = 3
    data['auctions'][0]['procurementMethodType'] = 'sellout.insider'
    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        headers=access_header,
        params={'data': data},
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['auctions'][0]['tenderAttempts'], 1)
    self.assertEqual(response.json['data']['auctions'][0]['procurementMethodType'], 'sellout.english')

    response = self.app.get('/{}/auctions'.format(lot['id']))
    auctions = sorted(response.json['data'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]
    self.assertEqual(english['tenderAttempts'], 1)
    self.assertEqual(english['procurementMethodType'], 'sellout.english')


def patch_auction_by_concierge(self):
    data = deepcopy(self.initial_auctions_data)
    response = self.app.get('/{}/auctions'.format(self.resource_id))
    auctions = sorted(response.json['data'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]
    data['english']['minimalStep']['amount'] = 99

    response = self.app.patch_json('/{}/auctions/{}'.format(self.resource_id, english['id']),
        headers=self.access_header, params={
            'data': data['english']
            })
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['id'], english['id'])
    self.assertEqual(response.json['data']['tenderAttempts'], 1)
    self.assertEqual(response.json['data']['value'], data['english']['value'])
    self.assertEqual(response.json['data']['minimalStep'], data['english']['minimalStep'])
    self.assertEqual(response.json['data']['auctionPeriod'], data['english']['auctionPeriod'])
    self.assertEqual(response.json['data']['guarantee'], data['english']['guarantee'])
    self.assertEqual(response.json['data']['registrationFee'], data['english']['registrationFee'])
    self.assertNotIn('dutchSteps', response.json['data']['auctionParameters'])

    self.app.authorization = ('Basic', ('concierge', ''))
    
    response = self.app.patch_json('/{}/auctions/{}'.format(self.resource_id, english['id']),
        headers=self.access_header, params={
            'data': {
                'status': 'unsuccessful',
                'auctionID': 'someAuctionID',
                'relatedProcessID': '1' * 32
            }
            })
    self.assertEqual(response.json['data']['status'], 'unsuccessful')
    self.assertEqual(response.json['data']['auctionID'], 'someAuctionID')
    self.assertEqual(response.json['data']['relatedProcessID'], '1' * 32)


def patch_english_auction(self):
    data = deepcopy(self.initial_auctions_data)
    response = self.app.get('/{}/auctions'.format(self.resource_id))
    auctions = sorted(response.json['data'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]
    data['english']['minimalStep']['amount'] = 99

    response = self.app.patch_json('/{}/auctions/{}'.format(self.resource_id, english['id']),
        headers=self.access_header, params={
            'data': data['english']
            })
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['id'], english['id'])
    self.assertEqual(response.json['data']['tenderAttempts'], 1)
    self.assertEqual(response.json['data']['value'], data['english']['value'])
    self.assertEqual(response.json['data']['minimalStep'], data['english']['minimalStep'])
    self.assertEqual(response.json['data']['auctionPeriod'], data['english']['auctionPeriod'])
    self.assertEqual(response.json['data']['guarantee'], data['english']['guarantee'])
    self.assertEqual(response.json['data']['registrationFee'], data['english']['registrationFee'])
    self.assertNotIn('dutchSteps', response.json['data']['auctionParameters'])
    default_type = response.json['data']['auctionParameters']['type']

    response = self.app.get('/{}/auctions'.format(self.resource_id))
    auctions = sorted(response.json['data'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]
    second_english = auctions[1]
    insider = auctions[2]

    # Test first sellout.english
    self.assertEqual(english['procurementMethodType'], 'sellout.english')
    self.assertEqual(english['value']['amount'], data['english']['value']['amount'])
    self.assertEqual(english['registrationFee']['amount'], data['english']['registrationFee']['amount'])
    self.assertEqual(english['minimalStep']['amount'], data['english']['minimalStep']['amount'])
    self.assertEqual(english['guarantee']['amount'], data['english']['guarantee']['amount'])
    self.assertEqual(english['auctionParameters']['type'], 'english')
    self.assertNotIn('dutchSteps', english['auctionParameters'])
    self.assertNotIn('tenderingDuration', english)

    # Test second sellout.english(half values)
    self.assertEqual(second_english['procurementMethodType'], 'sellout.english')
    self.assertEqual(second_english['value']['amount'], english['value']['amount'] / 2)
    self.assertEqual(second_english['registrationFee']['amount'], english['registrationFee']['amount'] / 2)
    self.assertEqual(second_english['minimalStep']['amount'], english['minimalStep']['amount'] / 2)
    self.assertEqual(second_english['guarantee']['amount'], english['guarantee']['amount'] / 2)
    self.assertEqual(second_english['auctionParameters']['type'], 'english')
    self.assertNotIn('dutchSteps', second_english['auctionParameters'])

    # Test second sellout.insider(half values)
    self.assertEqual(insider['procurementMethodType'], 'sellout.insider')
    self.assertEqual(insider['value']['amount'], english['value']['amount'] / 2)
    self.assertEqual(insider['registrationFee']['amount'], english['registrationFee']['amount'] / 2)
    self.assertEqual(insider['minimalStep']['amount'], 0)
    self.assertEqual(insider['guarantee']['amount'], english['guarantee']['amount'] / 2)
    self.assertEqual(insider['auctionParameters']['type'], 'insider')
    self.assertEqual(insider['auctionParameters']['dutchSteps'], DEFAULT_DUTCH_STEPS)

    # Test change tenderingDuration
    data['english']['minimalStep']['amount'] = 100
    data['english']['tenderingDuration'] = 'P2YT3H'
    response = self.app.patch_json('/{}/auctions/{}'.format(self.resource_id, english['id']),
        headers=self.access_header, params={
            'data': data['english']
            })
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['tenderAttempts'], 1)
    self.assertNotIn('tenderingDuration', response.json['data'])

    response = self.app.get('/{}/auctions'.format(self.resource_id))
    auctions = sorted(response.json['data'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]
    second_english = auctions[1]
    insider = auctions[2]

    # Test first sellout.english
    self.assertEqual(english['procurementMethodType'], 'sellout.english')
    self.assertEqual(english['value']['amount'], data['english']['value']['amount'])
    self.assertEqual(english['registrationFee']['amount'], data['english']['registrationFee']['amount'])
    self.assertEqual(english['minimalStep']['amount'], data['english']['minimalStep']['amount'])
    self.assertEqual(english['guarantee']['amount'], data['english']['guarantee']['amount'])
    self.assertEqual(english['auctionParameters']['type'], 'english')
    self.assertNotIn('dutchSteps', english['auctionParameters'])
    self.assertNotIn('tenderingDuration', english)

    # Test second sellout.english(half values)
    self.assertEqual(second_english['procurementMethodType'], 'sellout.english')
    self.assertEqual(second_english['value']['amount'], english['value']['amount'] / 2)
    self.assertEqual(second_english['registrationFee']['amount'], english['registrationFee']['amount'] / 2)
    self.assertEqual(second_english['minimalStep']['amount'], english['minimalStep']['amount'] / 2)
    self.assertEqual(second_english['guarantee']['amount'], english['guarantee']['amount'] / 2)
    self.assertEqual(second_english['auctionParameters']['type'], 'english')
    self.assertNotIn('dutchSteps', second_english['auctionParameters'])

    # Test second sellout.insider(half values)
    self.assertEqual(insider['procurementMethodType'], 'sellout.insider')
    self.assertEqual(insider['value']['amount'], english['value']['amount'] / 2)
    self.assertEqual(insider['registrationFee']['amount'], english['registrationFee']['amount'] / 2)
    self.assertEqual(insider['minimalStep']['amount'], 0)
    self.assertEqual(insider['guarantee']['amount'], english['guarantee']['amount'] / 2)
    self.assertEqual(insider['auctionParameters']['type'], 'insider')
    self.assertEqual(insider['auctionParameters']['dutchSteps'], DEFAULT_DUTCH_STEPS)

    # Test change steps validation
    data['english']['auctionParameters'] = {'dutchSteps': 66}
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(self.resource_id, english['id']),
        headers=self.access_header, params={
            'data': data['english']
            },
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json, None)

    response = self.app.get(
        '/{}/auctions/{}'.format(self.resource_id, english['id']),
        headers=self.access_header,
    )
    self.assertNotIn('dutchSteps', response.json['data']['auctionParameters'])

    # Test type validation
    data['english']['auctionParameters'] = {'type': 'insider'}
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(self.resource_id, english['id']),
        headers=self.access_header, params={
            'data': data['english']
            },
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json, None)


    response = self.app.get(
        '/{}/auctions/{}'.format(self.resource_id, english['id']),
        headers=self.access_header
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertNotEqual(response.json['data']['auctionParameters']['type'], data['english']['auctionParameters']['type'])
    self.assertEqual(response.json['data']['auctionParameters']['type'], default_type)


def patch_second_english_auction(self):
    data = deepcopy(self.initial_auctions_data)
    response = self.app.get('/{}/auctions'.format(self.resource_id))
    auctions = sorted(response.json['data'], key=lambda a: a['tenderAttempts'])
    second_english = auctions[1]
    second_english['tenderingDuration'] = 'P2YT3H'
    default_type = second_english['auctionParameters']['type']

    response = self.app.patch_json('/{}/auctions/{}'.format(self.resource_id, second_english['id']),
        headers=self.access_header, params={
            'data': data['second.english']
            })
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['tenderingDuration'], data['second.english']['tenderingDuration'])
    self.assertEqual(response.json['data']['tenderAttempts'], 2)
    self.assertNotIn('dutchSteps', response.json['data']['auctionParameters'])

    response = self.app.get('/{}/auctions'.format(self.resource_id))
    auctions = sorted(response.json['data'], key=lambda a: a['tenderAttempts'])
    second_english = auctions[1]
    insider = auctions[2]

    # Test second sellout.english(half values)
    self.assertEqual(second_english['auctionParameters']['type'], 'english')
    self.assertEqual(second_english['tenderingDuration'], data['second.english']['tenderingDuration'])
    self.assertNotIn('dutchSteps', second_english['auctionParameters'])

    # Test second sellout.insider(half values)
    self.assertEqual(insider['procurementMethodType'], 'sellout.insider')
    self.assertEqual(insider['tenderingDuration'], second_english['tenderingDuration'])
    self.assertEqual(insider['auctionParameters']['dutchSteps'], DEFAULT_DUTCH_STEPS)

    # Test dutch steps validation
    data = deepcopy(self.initial_auctions_data)
    data['second.english']['auctionParameters'] = {'dutchSteps': 66}
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(self.resource_id, second_english['id']),
        headers=self.access_header, params={
            'data': data['english']
            },
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json, None)

    response = self.app.get(
        '/{}/auctions/{}'.format(self.resource_id, second_english['id']),
        headers=self.access_header,
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertNotIn('dutchSteps', response.json['data']['auctionParameters'])

    # Test type validation
    data = deepcopy(self.initial_auctions_data)
    data['second.english']['auctionParameters'] = {'type': 'insider'}
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(self.resource_id, insider['id']),
        headers=self.access_header, params={
            'data': data['second.english']
            },
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json, None)

    response = self.app.get(
        '/{}/auctions/{}'.format(self.resource_id, second_english['id']),
        headers=self.access_header,
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertNotEqual(response.json['data']['auctionParameters']['type'],
                        data['second.english']['auctionParameters']['type'])
    self.assertEqual(response.json['data']['auctionParameters']['type'], default_type)


def patch_insider_auction(self):
    data = deepcopy(self.initial_auctions_data)
    response = self.app.get('/{}/auctions'.format(self.resource_id))
    auctions = sorted(response.json['data'], key=lambda a: a['tenderAttempts'])
    insider = auctions[2]
    data_dutch_steps = {'auctionParameters': {'dutchSteps': 77}}

    response = self.app.patch_json('/{}/auctions/{}'.format(self.resource_id, insider['id']),
        headers=self.access_header, params={
            'data': data_dutch_steps
            })
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['auctionParameters']['dutchSteps'], data_dutch_steps['auctionParameters']['dutchSteps'])
    self.assertNotIn('tenderingDuration', response.json['data'])
    self.assertEqual(response.json['data']['tenderAttempts'], 3)
    default_type = response.json['data']['auctionParameters']['type']

    data_with_tenderingDuration = {
        'tenderingDuration': 'P2YT3H',
        'auctionParameters': {'dutchSteps': 88}
    }
    response = self.app.patch_json('/{}/auctions/{}'.format(self.resource_id, insider['id']),
        headers=self.access_header, params={
            'data': data_with_tenderingDuration
            })
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertNotIn('tenderingDuration', response.json['data'])
    self.assertEqual(response.json['data']['tenderAttempts'], 3)

    # Test type validation
    data = deepcopy(self.initial_auctions_data)
    data['insider'] = {}
    data['insider']['auctionParameters'] = {'type': 'english'}
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(self.resource_id, insider['id']),
        headers=self.access_header, params={
            'data': data['english']
            },
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json, None)

    response = self.app.get(
        '/{}/auctions/{}'.format(self.resource_id, insider['id']),
        headers=self.access_header
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertNotEqual(response.json['data']['auctionParameters']['type'],
                        data['insider']['auctionParameters']['type'])
    self.assertEqual(response.json['data']['auctionParameters']['type'], default_type)


def rectificationPeriod_auction_workflow(self):
    rectificationPeriod = Period()
    rectificationPeriod.startDate = get_now() - timedelta(3)
    rectificationPeriod.endDate = calculate_business_date(rectificationPeriod.startDate,
                                                          timedelta(1),
                                                          None)
    data = deepcopy(self.initial_auctions_data)

    lot = self.create_resource()

    # Change rectification period in db
    fromdb = self.db.get(lot['id'])
    fromdb = Lot(fromdb)

    fromdb.status = 'pending'
    fromdb.rectificationPeriod = rectificationPeriod
    fromdb = fromdb.store(self.db)

    self.assertEqual(fromdb.id, lot['id'])

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['id'], lot['id'])

    response = self.app.get('/{}/auctions'.format(self.resource_id))
    auctions = sorted(response.json['data'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]


    response = self.app.patch_json('/{}/auctions/{}'.format(lot['id'], english['id']),
                                   headers=self.access_header,
                                   params={'data': data['english']},
                                   status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]['description'], 'You can\'t change auctions after rectification period')


@unittest.skipIf(not SANDBOX_MODE, 'If sandbox mode is enabled auctionParameters has additional field procurementMethodDetails')
def procurementMethodDetails_check_with_sandbox(self):
    # Test procurementMethodDetails after creating lot
    response = self.app.get('/{}'.format(self.resource_id))
    lot = response.json['data']
    english = response.json['data']['auctions'][0]
    second_english = response.json['data']['auctions'][1]
    insider = response.json['data']['auctions'][2]

    self.assertNotIn(
        'procurementMethodDetails',
        english
    )
    self.assertNotIn(
        'procurementMethodDetails',
        second_english
    )
    self.assertNotIn(
        'procurementMethodDetails',
        insider
    )

    auction_param_with_procurementMethodDetails = {'procurementMethodDetails': 'quick'}


    # Test procurementMethodDetails after update second english
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], second_english['id']),
        {'data': auction_param_with_procurementMethodDetails},
        headers=self.access_header
    )
    self.assertEqual(
        response.json['data']['procurementMethodDetails'],
        auction_param_with_procurementMethodDetails['procurementMethodDetails']
    )


    # Test procurementMethodDetails after update insider
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], insider['id']),
        {'data': auction_param_with_procurementMethodDetails},
        headers=self.access_header
    )
    self.assertEqual(
        response.json['data']['procurementMethodDetails'],
        auction_param_with_procurementMethodDetails['procurementMethodDetails']
    )



    # Test procurementMethodDetails after update english
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], english['id']),
        {'data': auction_param_with_procurementMethodDetails},
        headers=self.access_header
    )
    self.assertEqual(
        response.json['data']['procurementMethodDetails'],
        auction_param_with_procurementMethodDetails['procurementMethodDetails']
    )


@unittest.skipIf(SANDBOX_MODE, 'If sandbox mode is disabled auctionParameters has not procurementMethodDetails field')
def procurementMethodDetails_check_without_sandbox(self):
    # Test procurementMethodDetails after creating lot
    response = self.app.get('/{}'.format(self.resource_id))
    lot = response.json['data']
    english = response.json['data']['auctions'][0]
    second_english = response.json['data']['auctions'][1]
    insider = response.json['data']['auctions'][2]

    self.assertNotIn(
        'procurementMethodDetails',
        response.json['data']['auctions'][0],
    )
    self.assertNotIn(
        'procurementMethodDetails',
        response.json['data']['auctions'][1],
    )
    self.assertNotIn(
        'procurementMethodDetails',
        response.json['data']['auctions'][2],
    )


    auction_param_with_procurementMethodDetails = {'procurementMethodDetails': 'quick'}

    # Test procurementMethodDetails error while updating english
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], english['id']),
        {'data': auction_param_with_procurementMethodDetails},
        headers=self.access_header,
        status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description'], u'Rogue field')
    self.assertEqual(response.json['errors'][0]['name'], 'procurementMethodDetails')

    # Test procurementMethodDetails error while updating english
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], second_english['id']),
        {'data': auction_param_with_procurementMethodDetails},
        headers=self.access_header,
        status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description'], u'Rogue field')
    self.assertEqual(response.json['errors'][0]['name'], 'procurementMethodDetails')

    # Test procurementMethodDetails error while updating english
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], insider['id']),
        {'data': auction_param_with_procurementMethodDetails},
        headers=self.access_header,
        status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description'], u'Rogue field')
    self.assertEqual(response.json['errors'][0]['name'], 'procurementMethodDetails')


# submissionMethodDetails test
def submissionMethodDetails_check(self):
    # Test submissionMethodDetails after creating lot
    response = self.app.get('/{}'.format(self.resource_id))
    lot = response.json['data']
    english = response.json['data']['auctions'][0]
    second_english = response.json['data']['auctions'][1]
    insider = response.json['data']['auctions'][2]

    self.assertNotIn(
        'submissionMethodDetails',
        english
    )
    self.assertNotIn(
        'submissionMethodDetails',
         second_english
    )
    self.assertNotIn(
        'submissionMethodDetails',
        insider
    )

    auction_param_with_submissionMethodDetails = {'submissionMethodDetails': 'quick(mode:fast-forward)'}

    # Test submissionMethodDetails after update second english
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], second_english['id']),
        {'data': auction_param_with_submissionMethodDetails},
        headers=self.access_header
    )
    self.assertEqual(
        response.json['data']['submissionMethodDetails'],
        auction_param_with_submissionMethodDetails['submissionMethodDetails']
    )

    # Test submissionMethodDetails after update insider
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], insider['id']),
        {'data': auction_param_with_submissionMethodDetails},
        headers=self.access_header
    )
    self.assertEqual(
        response.json['data']['submissionMethodDetails'],
        auction_param_with_submissionMethodDetails['submissionMethodDetails']
    )

    # Test submissionMethodDetails after update english
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], english['id']),
        {'data': auction_param_with_submissionMethodDetails},
        headers=self.access_header
    )
    self.assertEqual(
        response.json['data']['submissionMethodDetails'],
        auction_param_with_submissionMethodDetails['submissionMethodDetails']
    )


def registrationFee_default(self):
    # Check default registrationFee.amount
    data = deepcopy(self.initial_auctions_data)
    response = self.app.get('/{}/auctions'.format(self.resource_id))
    auctions = sorted(response.json['data'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]
    second_english = auctions[1]
    insider = auctions[2]

    self.assertEqual(english['registrationFee']['amount'], DEFAULT_REGISTRATION_FEE)
    self.assertEqual(second_english['registrationFee']['amount'], DEFAULT_REGISTRATION_FEE / 2)
    self.assertEqual(insider['registrationFee']['amount'], DEFAULT_REGISTRATION_FEE / 2)

    # Change registrationFee
    data = {
        'registrationFee': {'amount': 100}
    }
    response = self.app.patch_json('/{}/auctions/{}'.format(self.resource_id, english['id']),
        headers=self.access_header, params={
            'data': data
            })
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['data']['registrationFee']['amount'],
        data['registrationFee']['amount']
    )

    response = self.app.get('/{}/auctions'.format(self.resource_id))
    auctions = sorted(response.json['data'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]
    second_english = auctions[1]
    insider = auctions[2]

    self.assertEqual(english['registrationFee']['amount'], data['registrationFee']['amount'])
    self.assertEqual(second_english['registrationFee']['amount'], data['registrationFee']['amount'] / 2)
    self.assertEqual(insider['registrationFee']['amount'], data['registrationFee']['amount'] / 2)

    # Patch registrationFee to None
    data = {
        'registrationFee': None
    }
    response = self.app.patch_json('/{}/auctions/{}'.format(self.resource_id, english['id']),
        headers=self.access_header, params={
            'data': data
            })
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['registrationFee']['amount'], DEFAULT_REGISTRATION_FEE)

    response = self.app.get('/{}/auctions'.format(self.resource_id))
    auctions = sorted(response.json['data'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]
    second_english = auctions[1]
    insider = auctions[2]

    self.assertEqual(english['registrationFee']['amount'], DEFAULT_REGISTRATION_FEE)
    self.assertEqual(second_english['registrationFee']['amount'], DEFAULT_REGISTRATION_FEE / 2)
    self.assertEqual(insider['registrationFee']['amount'], DEFAULT_REGISTRATION_FEE / 2)

