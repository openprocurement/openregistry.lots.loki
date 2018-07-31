 # -*- coding: utf-8 -*-
import unittest

from copy import deepcopy
from uuid import uuid4
from datetime import timedelta
from isodate import parse_datetime

from openregistry.lots.core.utils import get_now, calculate_business_date
from openregistry.lots.core.models import Period
from openregistry.lots.core.tests.base import create_blacklist
from openregistry.lots.core.constants import (
    SANDBOX_MODE,
)

from openregistry.lots.loki.models import Lot
from openregistry.lots.loki.tests.json_data import (
    auction_english_data,
    auction_second_english_data,
    test_loki_item_data
)
from openregistry.lots.loki.constants import (
    STATUS_CHANGES,
    LOT_STATUSES,
    DEFAULT_DUTCH_STEPS,
    RECTIFICATION_PERIOD_DURATION,
    DAYS_AFTER_RECTIFICATION_PERIOD,
    PLATFORM_LEGAL_DETAILS_DOC_DATA
)
from openregistry.lots.loki.tests.base import (
    create_single_lot,
    check_patch_status_200,
    check_patch_status_403,
    add_decisions,
    add_auctions,
    add_lot_decision,
    DEFAULT_ACCELERATION
)

ROLES = ['lot_owner', 'Administrator', 'concierge', 'convoy', 'chronograph']
STATUS_BLACKLIST = create_blacklist(STATUS_CHANGES, LOT_STATUSES, ROLES)


# LotTest
def simple_add_lot(self):
    u = Lot(self.initial_data)
    u.lotID = "UA-X"
    u.assets = [uuid4().hex]

    assert u.id is None
    assert u.rev is None

    u.store(self.db)

    assert u.id is not None
    assert u.rev is not None

    fromdb = self.db.get(u.id)

    assert u.lotID == fromdb['lotID']
    assert u.doc_type == "Lot"

    u.delete_instance(self.db)


def add_cancellationDetails_document(self, lot, access_header):
    # Add cancellationDetails document
    test_document_data = {
        # 'url': self.generate_docservice_url(),
        'title': u'укр.doc',
        'hash': 'md5:' + '0' * 32,
        'format': 'application/msword',
        'documentType': 'cancellationDetails'
    }
    test_document_data['url'] = self.generate_docservice_url()

    response = self.app.post_json('/{}/documents'.format(lot['id']),
                                  headers=access_header,
                                  params={'data': test_document_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual(u'укр.doc', response.json["data"]["title"])
    self.assertIn('Signature=', response.json["data"]["url"])
    self.assertIn('KeyID=', response.json["data"]["url"])
    self.assertNotIn('Expires=', response.json["data"]["url"])
    key = response.json["data"]["url"].split('/')[-1].split('?')[0]
    tender = self.db.get(lot['id'])
    self.assertIn(key, tender['documents'][-1]["url"])
    self.assertIn('Signature=', tender['documents'][-1]["url"])
    self.assertIn('KeyID=', tender['documents'][-1]["url"])
    self.assertNotIn('Expires=', tender['documents'][-1]["url"])


def auction_autocreation(self):
    response = self.app.post_json('/', {"data": self.initial_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], 'draft')
    self.assertEqual(len(response.json['data']['auctions']), 3)
    auctions = sorted(response.json['data']['auctions'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]
    second_english = auctions[1]
    insider = auctions[2]

    self.assertEqual(english['procurementMethodType'], 'sellout.english')
    self.assertEqual(english['tenderAttempts'], 1)
    self.assertEqual(english['status'], 'scheduled')
    self.assertEqual(english['auctionParameters']['type'], 'english')

    self.assertEqual(second_english['procurementMethodType'], 'sellout.english')
    self.assertEqual(second_english['tenderAttempts'], 2)
    self.assertEqual(second_english['status'], 'scheduled')
    self.assertEqual(second_english['auctionParameters']['type'], 'english')

    self.assertEqual(insider['procurementMethodType'], 'sellout.insider')
    self.assertEqual(insider['tenderAttempts'], 3)
    self.assertEqual(insider['status'], 'scheduled')
    self.assertEqual(insider['auctionParameters']['type'], 'insider')
    self.assertEqual(insider['auctionParameters']['dutchSteps'], DEFAULT_DUTCH_STEPS)


def check_change_to_verification(self):
    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    draft_lot['assets'] = [uuid4().hex]
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'draft')

    response = self.app.get('/{}/auctions'.format(lot['id']))
    auctions = sorted(response.json['data'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]
    second_english = auctions[1]

    first_english_data = deepcopy(auction_english_data)
    first_english_data['auctionPeriod']['startDate'] = get_now().isoformat()


    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], lot)

    # Move from 'draft' to 'draft' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'draft', access_header)

    # Move from 'draft' to 'composing' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    lot = add_lot_decision(self, lot['id'], access_header)

    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        {"data": {'status': 'verification'}},
        status=422,
        headers=access_header
    )
    # Check if all required fields are filled in first english auction
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['name'],
        'auctions'
    )
    self.assertEqual(
        response.json['errors'][0]['description'][0],
        {
            'value': ['This field is required.'],
            'minimalStep': ['This field is required.'],
            'auctionPeriod': ['This field is required.'],
            'guarantee': ['This field is required.'],
            'bankAccount': ['This field is required.'],
        }
    )
    self.assertEqual(
        response.json['errors'][0]['description'][1],
        {
            'tenderingDuration': ['This field is required.'],
        }
    )

    first_english_data_without_bankAccount = deepcopy(first_english_data)
    del first_english_data_without_bankAccount['bankAccount']
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], english['id']),
        params={'data': first_english_data_without_bankAccount}, headers=access_header)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        {"data": {'status': 'verification'}},
        status=422,
        headers=access_header
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'][0],
        {
            'bankAccount': ['This field is required.']
        }
    )

    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], english['id']),
        params={'data': first_english_data}, headers=access_header)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    # Check if all required fields are filled in second english auction
    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        {"data": {'status': 'verification'}},
        status=422,
        headers=access_header
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'][0],
        {
            'tenderingDuration': ['This field is required.'],
        }
    )
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], second_english['id']),
        params={'data': auction_second_english_data}, headers=access_header)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    # Check if auctionPeriod.startDate is in three days after now
    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        {"data": {'status': 'verification'}},
        status=422,
        headers=access_header
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'startDate of auctionPeriod must be at least '
        'in {} days after today'.format((RECTIFICATION_PERIOD_DURATION + DAYS_AFTER_RECTIFICATION_PERIOD).days)
    )

    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], english['id']),
        params={'data': auction_english_data}, headers=access_header)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    # Check when decisions not available
    self.app.authorization = ('Basic', ('broker', ''))

    response = create_single_lot(self, self.initial_data)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    add_auctions(self, lot, access_header)
    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        {"data": {'status': 'verification'}},
        status=403,
        headers=access_header
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'Can\'t switch to verification while lot decisions not available.'
    )
    lot = add_lot_decision(self, lot['id'], access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    self.app.authorization = ('Basic', ('concierge', ''))

    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        headers=access_header,
        params={'data': {'status': 'pending'}},
        status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'Can\'t switch to pending while decisions not available.'
    )
    add_decisions(self, lot)
    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        headers=access_header,
        params={'data': {'status': 'pending'}},
        status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'Can\'t switch to pending while items in asset not available.'
    )


def rectificationPeriod_workflow(self):
    response = create_single_lot(self, self.initial_data)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    self.assertNotIn('rectificationPeriod', response.json['data'])
    self.assertNotIn('next_check', response.json['data'])

    response = self.app.patch_json('/{}'.format(lot['id']),
                                   headers=access_header,
                                   params={'data': {'status': 'composing'}})
    self.assertNotIn('rectificationPeriod', response.json['data'])
    self.assertNotIn('next_check', response.json['data'])

    lot = add_lot_decision(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)
    response = self.app.patch_json('/{}'.format(lot['id']),
                                   headers=access_header,
                                   params={'data': {'status': 'verification'}})
    self.assertNotIn('rectificationPeriod', response.json['data'])
    self.assertNotIn('next_check', response.json['data'])

    self.app.authorization = ('Basic', ('concierge', ''))
    add_decisions(self, lot)
    response = self.app.patch_json('/{}'.format(lot['id']),
                                   params={'data': {'status': 'pending', 'items': [test_loki_item_data]}})
    self.assertIn('rectificationPeriod', response.json['data'])
    startDate = parse_datetime(response.json['data']['rectificationPeriod']['startDate'])
    endDate = parse_datetime(response.json['data']['rectificationPeriod']['endDate'])
    accelerator = DEFAULT_ACCELERATION if SANDBOX_MODE else 1
    self.assertEqual(endDate - startDate, RECTIFICATION_PERIOD_DURATION/accelerator)
    self.assertEqual(response.json['data']['next_check'], response.json['data']['rectificationPeriod']['endDate'])

    response = self.app.get('/{}'.format(lot['id']))
    lot = response.json['data']

    # Check if chronograph come earlier than next_check
    self.app.authorization = ('Basic', ('chronograph', ''))
    response = self.app.patch_json('/{}'.format(lot['id']),
                                   headers=access_header,
                                   params={'data': {'status': 'active.salable'}})
    self.assertNotEqual(response.json['data']['status'], 'active.salable')
    self.assertEqual(lot['status'], response.json['data']['status'])

    # Check if auctionPeriod.StartDate is not in two days after rectificationPeriod.endDate
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.get('/{}/auctions'.format(lot['id']))
    auctions = sorted(response.json['data'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], english['id']),
        headers=access_header, params={
            'data': {'auctionPeriod': {'startDate': get_now().isoformat()}}
            },
        status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'][0],
        'startDate of auctionPeriod must be '
        'at least in {} days after endDate of rectificationPeriod'.format(DAYS_AFTER_RECTIFICATION_PERIOD.days)
    )

    rectificationPeriod = Period()
    rectificationPeriod.startDate = get_now() - timedelta(3)
    rectificationPeriod.endDate = calculate_business_date(rectificationPeriod.startDate,
                                                          timedelta(1),
                                                          None)

    response = create_single_lot(self, self.initial_data)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['id'], lot['id'])

    # Change rectification period in db
    add_auctions(self, lot, access_header)
    fromdb = self.db.get(lot['id'])
    fromdb = self.lot_model(fromdb)

    fromdb.status = 'pending'
    fromdb.decisions = [
        {
            'decisionDate': get_now().isoformat(),
            'decisionID': 'decisionAssetID'
        },
        {
            'decisionDate': get_now().isoformat(),
            'decisionID': 'decisionAssetID'
        }
    ]
    fromdb.title = 'title'
    fromdb.rectificationPeriod = rectificationPeriod
    fromdb = fromdb.store(self.db)
    lot = fromdb
    self.assertEqual(fromdb.id, lot['id'])

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['id'], lot['id'])

    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.patch_json('/{}'.format(lot['id']),
                                   headers=access_header,
                                   params={'data': {'title': 'PATCHED'}})
    self.assertNotEqual(response.json['data']['title'], 'PATCHED')
    self.assertEqual(lot['title'], response.json['data']['title'])

    add_cancellationDetails_document(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.deleted', access_header)


    # Check chronograph action
    self.app.authorization = ('Basic', ('broker', ''))

    response = create_single_lot(self, self.initial_data)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['id'], lot['id'])

    # Change rectification period in db
    add_auctions(self, lot, access_header)
    fromdb = self.db.get(lot['id'])
    fromdb = self.lot_model(fromdb)

    fromdb.status = 'pending'
    fromdb.decisions = [
        {
            'decisionDate': get_now().isoformat(),
            'decisionID': 'decisionAssetID'
        },
        {
            'decisionDate': get_now().isoformat(),
            'decisionID': 'decisionAssetID'
        }
    ]
    fromdb.title = 'title'
    fromdb.rectificationPeriod = rectificationPeriod
    fromdb = fromdb.store(self.db)
    lot = fromdb
    self.assertEqual(fromdb.id, lot['id'])

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['id'], lot['id'])

    self.app.authorization = ('Basic', ('chronograph', ''))
    response = self.app.patch_json('/{}'.format(lot['id']),
                                   params={'data': {'title': ' PATCHED'}})
    self.assertNotEqual(response.json['data']['title'], 'PATCHED')
    self.assertEqual(lot['title'], response.json['data']['title'])
    self.assertEqual(response.json['data']['status'], 'active.salable')
    self.assertNotIn('next_check', response.json['data'])


def dateModified_resource(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    response = self.app.post_json('/', {'data': self.initial_data})
    self.assertEqual(response.status, '201 Created')
    resource = response.json['data']

    token = str(response.json['access']['token'])
    dateModified = resource['dateModified']

    response = self.app.get('/{}'.format(resource['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['dateModified'], dateModified)

    response = self.app.patch_json('/{}'.format(resource['id']),
        headers={'X-Access-Token': token}, params={
            'data': {'status': 'composing'}
    })
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], 'composing')

    self.assertNotEqual(response.json['data']['dateModified'], dateModified)
    resource = response.json['data']
    dateModified = resource['dateModified']

    response = self.app.get('/{}'.format(resource['id']))

    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], resource)
    self.assertEqual(response.json['data']['dateModified'], dateModified)


def simple_patch(self):
    data = deepcopy(self.initial_data)
    response = create_single_lot(self, data)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(set(response.json['data']), set(lot))
    self.assertEqual(response.json['data'], lot)

    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    lot = add_lot_decision(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)


    self.app.authorization = ('Basic', ('concierge', ''))
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', extra={'items': [test_loki_item_data]})

    self.app.authorization = ('Basic', ('broker', ''))
    patch_data = {
        'data': {
            'officialRegistrationID': u'Інформація про державну реєстрацію'
        }
    }
    response = self.app.patch_json('/{}'.format(lot['id']), patch_data, headers=access_header)
    self.assertEqual(response.json['data']['officialRegistrationID'], patch_data['data']['officialRegistrationID'])


def check_lot_assets(self):

    # lot with a single assets
    self.initial_data["assets"] = [uuid4().hex]
    lot = create_single_lot(self, self.initial_data).json['data']
    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(set(response.json['data']), set(lot))
    self.assertEqual(response.json['data'], lot)

    # # lot with no assets
    self.initial_data["assets"] = []
    response = self.app.post_json('/', {"data": self.initial_data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u"Please provide at least 1 item."], u'location': u'body', u'name': u'assets'}
    ])


def change_draft_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    draft_lot['assets'] = [uuid4().hex]
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'draft')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], lot)

    # Move from 'draft' to 'draft' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'draft', access_header)

    # Move from 'draft' to 'pending' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)

    # Create lot in draft status
    draft_lot = deepcopy(draft_lot)
    draft_lot['status'] = 'draft'
    lot = create_single_lot(self, draft_lot).json['data']

    # Move from 'draft' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['draft']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)


    self.app.authorization = ('Basic', ('concierge', ''))

    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    draft_lot['status'] = 'draft'
    response = self.app.post_json('/', {'data': draft_lot}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')

    # Move from 'draft' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['draft']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))

    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    draft_lot['status'] = 'draft'
    response = self.app.post_json('/', {'data': draft_lot}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')

    # Move from 'draft' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['draft']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('convoy', ''))

    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    draft_lot['status'] = 'draft'
    response = self.app.post_json('/', {'data': draft_lot}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')

    # Move from 'draft' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['draft']['convoy']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))

    # Create lot in 'draft' status
    draft_lot = deepcopy(draft_lot)
    draft_lot['status'] = 'draft'
    response = self.app.post_json('/', {'data': draft_lot}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')

    # Move from 'draft' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['draft']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    # Move from 'draft' to 'draft' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'draft')

    # Move from 'draft' to 'composing' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing')


def change_composing_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    draft_lot['assets'] = [uuid4().hex]
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'draft')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], lot)

    # Move from 'draft' to 'draft' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'draft', access_header)

    # Move from 'draft' to 'composing' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)

    # Move from 'verification' to 'composing' status
    lot = add_lot_decision(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    draft_lot['assets'] = [uuid4().hex]
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'draft')

    # Move from 'draft' to 'composing' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)

    # Move from 'composing' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['composing']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)


    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['composing']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['composing']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'draft' to 'composing' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)


    self.app.authorization = ('Basic', ('broker', ''))
    lot = add_lot_decision(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)


    self.app.authorization = ('Basic', ('administrator', ''))
    # Move from 'verification' to 'composing' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    # Create lot in 'draft' status
    self.app.authorization = ('Basic', ('broker', ''))
    draft_lot = deepcopy(self.initial_data)
    draft_lot['assets'] = [uuid4().hex]
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'draft')

    # Move from 'draft' to 'composing' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)

    self.app.authorization = ('Basic', ('administrator', ''))
    for status in STATUS_BLACKLIST['composing']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_verification_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    draft_lot['assets'] = [uuid4().hex]
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'draft')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], lot)

    # Move from 'draft' to 'draft' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'draft', access_header)

    # Move from 'draft' to 'composing' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)

    # Move from 'composing' to 'verification' status
    lot = add_lot_decision(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    # Move from 'verification' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['verification']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['verification']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    # Move from 'verification' to 'pending' status
    self.app.authorization = ('Basic', ('concierge', ''))
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', extra={'items': [test_loki_item_data]})


    self.app.authorization = ('Basic', ('broker', ''))
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    lot = add_lot_decision(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    # Move from 'verification' to 'invalid' status
    self.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'invalid')


    self.app.authorization = ('Basic', ('broker', ''))
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    lot = add_lot_decision(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    # Move from 'verification' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['verification']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))
    # Move from 'verification' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['verification']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('broker', ''))
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    add_auctions(self, lot, access_header)
    add_lot_decision(self, lot['id'], access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    # Move from 'verification' to 'composing' status
    self.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing')


def change_pending_lot(self):

    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)


    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = deepcopy(self.initial_data)
    lot_info['status'] = 'draft'

    # Create lot in 'draft' status and move it to 'pending'
    response = create_single_lot(self, lot_info)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    response = self.app.get('/{}'.format(lot['id']), headers=access_header)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], lot)

    # Move from 'draft' to 'pending' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    lot = add_lot_decision(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)


    self.app.authorization = ('Basic', ('concierge', ''))

    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification')
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', extra={'items': [test_loki_item_data]})

    self.app.authorization = ('Basic', ('broker', ''))

    # Move from 'pending' to 'pending' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', access_header)

    # Move status from Pending to Deleted 403
    response = self.app.patch_json('/{}'.format(lot['id']),
                                   headers=access_header,
                                   params={'data': {'status': 'pending.deleted'}},
                                   status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'],
                    u"You can set deleted status "
                    u"only when lot have at least one document with \'cancellationDetails\' documentType")


    # Move from 'pending' to 'deleted' status
    add_cancellationDetails_document(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.deleted', access_header)

    # Create lot in 'draft' status and move it to 'pending'
    self.app.authorization = ('Basic', ('broker', ''))
    response = create_single_lot(self, deepcopy(lot_info))
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    lot = response.json['data']

    # Move from 'draft' to 'composing' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    lot = add_lot_decision(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    # Move from 'composing' to 'pending' status
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', extra={'items': [test_loki_item_data]})


    # Move from 'pending' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['pending']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)


    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'pending' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['pending']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['pending']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)
    # Chronograph patch but earlier than next_check
    response = self.app.patch_json('/{}'.format(lot['id']),
                                   params={'data': {'status': 'active.salable'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertNotEqual(response.json['data']['status'], 'active.salable')
    self.assertEqual(response.json['data']['status'], 'pending')


    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'pending' to 'pending' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending')

    # Move from 'pending' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['pending']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    # Move status from Pending to Deleted 403
    response = self.app.patch_json('/{}'.format(lot['id']),
                                   params={'data': {'status': 'pending.deleted'}},
                                   status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'],
                    u"You can set deleted status "
                    u"only when lot have at least one document with \'cancellationDetails\' documentType")


    # Move from 'pending' to 'deleted'
    self.app.authorization = ('Basic', ('broker', ''))
    add_cancellationDetails_document(self, lot, access_header)
    self.app.authorization = ('Basic', ('administrator', ''))

    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.deleted')

    # Create lot in 'draft' status and move it to 'pending'
    self.app.authorization = ('Basic', ('broker', ''))
    response = create_single_lot(self, deepcopy(lot_info))
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    lot = response.json['data']

    # Move from 'draft' to 'composing' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    lot = add_lot_decision(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    # Move from 'verification' to 'pending' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification')
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', extra={'items': [test_loki_item_data]})


    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'pending' to 'active.salable' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.salable', access_header)


def change_deleted_lot(self):

    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)


    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data
    lot_info['status'] = 'draft'

    # Create new lot in 'draft' status
    response = create_single_lot(self, lot_info)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'draft')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], lot)


    # Move from 'draft' to 'composing'
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    lot = add_lot_decision(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)


    self.app.authorization = ('Basic', ('concierge', ''))
    # Move from 'composing' to 'pending' status
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', extra={'items': [test_loki_item_data]})


    self.app.authorization = ('Basic', ('broker', ''))

    # Move from 'pending' to 'deleted'
    add_cancellationDetails_document(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.deleted', access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'deleted', access_header)

    self.app.authorization = ('Basic', ('broker', ''))
    # Move from 'deleted' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['deleted']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)


    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'deleted' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['deleted']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['deleted']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'deleted' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['deleted']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_active_salable_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)


    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'active.salable' status
    json = create_single_lot(self, lot_info, 'active.salable')
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'active.salable')

    self.app.authorization = ('Basic', ('broker', ''))

    # Move from 'active.salable' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['active.salable']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'active.salable' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['active.salable']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.auction')

    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.salable')
    lot = json['data']
    self.assertEqual(lot['status'], 'active.salable')

    self.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing')
    response = self.app.get('/{}'.format(lot['id']))
    self.assertNotIn('rectificationPeriod', response.json['data'])

    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.salable')
    lot = json['data']
    self.assertEqual(lot['status'], 'active.salable')

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['active.salable']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'active.salable' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['active.salable']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.auction')

    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.salable')
    lot = json['data']
    self.assertEqual(lot['status'], 'active.salable')

    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing')
    response = self.app.get('/{}'.format(lot['id']))
    self.assertNotIn('rectificationPeriod', response.json['data'])


def change_active_auction_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)


    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'active.auction' status
    json = create_single_lot(self, lot_info, 'active.auction')
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'active.auction')

    # Move from 'active.auction' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('broker', ''))
    for status in STATUS_BLACKLIST['active.auction']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    # Move from 'active.auction' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['active.auction']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['active.auction']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.salable')
    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.auction')
    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.contracting')

    # Create new lot in 'active.auction' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.auction')
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'active.auction')

    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.dissolution')


    # Create new lot in 'active.auction' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.auction')
    lot = json['data']
    token = json['access']['token']
    self.assertEqual(lot['status'], 'active.auction')


    # Move from 'active.auction' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('administrator', ''))
    for status in STATUS_BLACKLIST['active.auction']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_active_contracting_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)


    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'active.contracting' status
    json = create_single_lot(self, lot_info, 'active.contracting')
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'active.contracting')

    # Move from 'active.contracting' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('broker', ''))
    for status in STATUS_BLACKLIST['active.contracting']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    # Move from 'active.contracting' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['active.contracting']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['active.contracting']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.sold')

    # Create new lot in 'active.contracting' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.contracting')
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'active.contracting')

    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.dissolution')


    # Create new lot in 'active.contracting' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.contracting')
    lot = json['data']
    token = json['access']['token']
    self.assertEqual(lot['status'], 'active.contracting')


    # Move from 'active.contracting' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('administrator', ''))
    for status in STATUS_BLACKLIST['active.contracting']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_pending_sold_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)


    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'pending.sold' status
    json = create_single_lot(self, lot_info, 'pending.sold')
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'pending.sold')

    # Move from 'pending.sold' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('broker', ''))
    for status in STATUS_BLACKLIST['pending.sold']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'sold')


    # Create new lot in 'pending.sold' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'pending.sold')
    lot = json['data']
    token = json['access']['token']
    self.assertEqual(lot['status'], 'pending.sold')


    # Move from 'pending.sold' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['pending.sold']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['pending.sold']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'sold')


    # Create new lot in 'pending.sold' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'pending.sold')
    lot = json['data']
    token = json['access']['token']
    self.assertEqual(lot['status'], 'pending.sold')


def change_pending_dissolution_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)


    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'pending.dissolution' status
    json = create_single_lot(self, lot_info, 'pending.dissolution')
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'pending.dissolution')

    # Move from 'pending.dissolution' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('broker', ''))
    for status in STATUS_BLACKLIST['pending.dissolution']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)


    self.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'dissolved')


    # Create new lot in 'pending.dissolution' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'pending.dissolution')
    lot = json['data']
    token = json['access']['token']
    self.assertEqual(lot['status'], 'pending.dissolution')

    # Move from 'pending.dissolution' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['pending.dissolution']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['pending.dissolution']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'dissolved')


    # Create new lot in 'pending.dissolution' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'pending.dissolution')
    lot = json['data']
    token = json['access']['token']
    self.assertEqual(lot['status'], 'pending.dissolution')

    # Move from 'pending.dissolution' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('administrator', ''))
    for status in STATUS_BLACKLIST['pending.dissolution']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_sold_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)


    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'sold' status
    json = create_single_lot(self, lot_info, 'sold')
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'sold')

    # Move from 'sold' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['sold']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)


    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'sold' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['sold']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['sold']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'sold' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['sold']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_dissolved_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)


    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'dissolved' status
    json = create_single_lot(self, lot_info, 'dissolved')
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'dissolved')

    # Move from 'dissolved' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['dissolved']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)


    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'dissolved' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['dissolved']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['dissolved']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'dissolved' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['dissolved']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_invalid_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)


    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'dissolved' status
    json = create_single_lot(self, lot_info, 'invalid')
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'invalid')

    # Move from 'invalid' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['invalid']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)


    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'invalid' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['invalid']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['invalid']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'invalid' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['invalid']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_pending_deleted_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'pending.deleted' status
    json = create_single_lot(self, lot_info, 'composing')
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    lot = add_lot_decision(self, lot['id'], access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', extra={'items': [test_loki_item_data]})
    self.app.authorization = ('Basic', ('broker', ''))
    add_cancellationDetails_document(self, lot, access_header)

    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.deleted', access_header)

    # Move from 'pending.deleted' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('broker', ''))
    for status in STATUS_BLACKLIST['pending.deleted']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'deleted')
    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['auctions'][0]['status'], 'cancelled')
    self.assertEqual(response.json['data']['auctions'][1]['status'], 'cancelled')
    self.assertEqual(response.json['data']['auctions'][2]['status'], 'cancelled')
    self.assertEqual(response.json['data']['contracts'][0]['status'], 'cancelled')

    # Create new lot in 'pending.deleted' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'composing')
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    lot = add_lot_decision(self, lot['id'], access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', extra={'items': [test_loki_item_data]})
    self.app.authorization = ('Basic', ('broker', ''))
    add_cancellationDetails_document(self, lot, access_header)

    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.deleted', access_header)

    # Move from 'pending.deleted' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['pending.deleted']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['pending.deleted']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'deleted')
    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['auctions'][0]['status'], 'cancelled')
    self.assertEqual(response.json['data']['auctions'][1]['status'], 'cancelled')
    self.assertEqual(response.json['data']['auctions'][2]['status'], 'cancelled')
    self.assertEqual(response.json['data']['contracts'][0]['status'], 'cancelled')

    # Create new lot in 'pending.deleted' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'pending.deleted')
    lot = json['data']
    token = json['access']['token']
    self.assertEqual(lot['status'], 'pending.deleted')

    # Move from 'pending.deleted' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('administrator', ''))
    for status in STATUS_BLACKLIST['pending.deleted']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def check_auction_status_lot_workflow(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)


    lot_info = self.initial_data

    # Create new lot in 'active.auction' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.auction')
    lot = json['data']
    self.assertEqual(lot['status'], 'active.auction')
    auctions = sorted(lot['auctions'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]


    self.app.authorization = ('Basic', ('convoy', ''))
    response = self.app.patch_json('/{}/auctions/{}'.format(lot['id'], english['id']),
                                   params={'data': {'status': 'unsuccessful'}})
    self.assertEqual(response.json['data']['status'], 'unsuccessful')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['status'], 'active.salable')
    auctions = sorted(response.json['data']['auctions'], key=lambda a: a['tenderAttempts'])
    contract = response.json['data']['contracts'][0]

    self.assertEqual(auctions[0]['status'], 'unsuccessful')
    self.assertEqual(auctions[1]['status'], 'scheduled')
    self.assertEqual(auctions[2]['status'], 'scheduled')
    self.assertEqual(contract['status'], 'scheduled')


    # Create new lot in 'active.auction' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.auction')
    lot = json['data']
    self.assertEqual(lot['status'], 'active.auction')

    auctions = sorted(lot['auctions'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]

    self.app.authorization = ('Basic', ('convoy', ''))
    response = self.app.patch_json('/{}/auctions/{}'.format(lot['id'], english['id']),
                                   params={'data': {'status': 'cancelled'}})
    self.assertEqual(response.json['data']['status'], 'cancelled')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['status'], 'pending.dissolution')
    auctions = sorted(response.json['data']['auctions'], key=lambda a: a['tenderAttempts'])
    contract = response.json['data']['contracts'][0]

    self.assertEqual(auctions[0]['status'], 'cancelled')
    self.assertEqual(auctions[1]['status'], 'cancelled')
    self.assertEqual(auctions[2]['status'], 'cancelled')
    self.assertEqual(contract['status'], 'cancelled')

    # Create new lot in 'active.auction' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.auction')
    lot = json['data']
    self.assertEqual(lot['status'], 'active.auction')

    auctions = sorted(lot['auctions'], key=lambda a: a['tenderAttempts'])
    insider = auctions[2]

    # Change statuses of two first auctions to unsuccessful
    fromdb = self.db.get(lot['id'])
    fromdb = self.lot_model(fromdb)

    fromdb.auctions[0].status = 'unsuccessful'
    fromdb.auctions[1].status = 'unsuccessful'
    fromdb = fromdb.store(self.db)
    lot = fromdb
    self.assertEqual(fromdb.id, lot['id'])


    self.app.authorization = ('Basic', ('convoy', ''))
    response = self.app.patch_json('/{}/auctions/{}'.format(lot['id'], insider['id']),
                                   params={'data': {'status': 'unsuccessful'}})

    self.assertEqual(response.json['data']['status'], 'unsuccessful')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['status'], 'pending.dissolution')
    auctions = sorted(response.json['data']['auctions'], key=lambda a: a['tenderAttempts'])
    contract = response.json['data']['contracts'][0]

    self.assertEqual(auctions[0]['status'], 'unsuccessful')
    self.assertEqual(auctions[1]['status'], 'unsuccessful')
    self.assertEqual(auctions[2]['status'], 'unsuccessful')
    self.assertEqual(contract['status'], 'cancelled')

    # Create new lot in 'active.salable' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.salable')
    lot = json['data']
    self.assertEqual(lot['status'], 'active.salable')
    auctions = sorted(lot['auctions'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]

    self.app.authorization = ('Basic', ('concierge', ''))
    response = self.app.patch_json('/{}/auctions/{}'.format(lot['id'], english['id']),
                                   params={'data': {'status': 'active'}})
    self.assertEqual(response.json['data']['status'], 'active')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['status'], 'active.auction')

    # Create new lot in 'active.auction' status and patch to complete
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.auction')
    lot = json['data']
    self.assertEqual(lot['status'], 'active.auction')
    auctions = sorted(lot['auctions'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]

    self.app.authorization = ('Basic', ('convoy', ''))
    response = self.app.patch_json('/{}/auctions/{}'.format(lot['id'], english['id']),
                                   params={'data': {'status': 'complete'}})
    self.assertEqual(response.json['data']['status'], 'complete')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['status'], 'active.contracting')
    auctions = sorted(response.json['data']['auctions'], key=lambda a: a['tenderAttempts'])

    self.assertEqual(auctions[0]['status'], 'complete')
    self.assertEqual(auctions[1]['status'], 'cancelled')
    self.assertEqual(auctions[2]['status'], 'cancelled')


def check_contract_status_workflow(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    lot_info = self.initial_data

    # Create new lot in 'active.contracting' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.contracting')
    lot = json['data']
    contract_id = lot['contracts'][0]['id']
    self.assertEqual(lot['status'], 'active.contracting')

    self.app.authorization = ('Basic', ('caravan', ''))
    response = self.app.patch_json('/{}/contracts/{}'.format(lot['id'], contract_id),
                                   params={'data': {'status': 'unsuccessful'}})

    self.assertEqual(response.json['data']['status'], 'unsuccessful')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['status'], 'pending.dissolution')

    contract = response.json['data']['contracts'][0]
    self.assertEqual(contract['status'], 'unsuccessful')

    # Create new lot in 'active.contracting' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.contracting')
    lot = json['data']
    contract_id = lot['contracts'][0]['id']
    self.assertEqual(lot['status'], 'active.contracting')

    self.app.authorization = ('Basic', ('caravan', ''))
    response = self.app.patch_json('/{}/contracts/{}'.format(lot['id'], contract_id),
                                   params={'data': {'status': 'complete'}})

    self.assertEqual(response.json['data']['status'], 'complete')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['status'], 'pending.sold')

    contract = response.json['data']['contracts'][0]
    self.assertEqual(contract['status'], 'complete')


def adding_platformLegalDetails_doc(self):
    response = self.app.post_json('/', {'data': self.initial_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(len(response.json['data']['documents']), 1)
    document = response.json['data']['documents'][0]
    self.assertEqual(document['title'], PLATFORM_LEGAL_DETAILS_DOC_DATA['title'])
    self.assertEqual(document['url'], PLATFORM_LEGAL_DETAILS_DOC_DATA['url'])
    self.assertEqual(document['documentOf'], PLATFORM_LEGAL_DETAILS_DOC_DATA['documentOf'])
    self.assertEqual(document['documentType'], PLATFORM_LEGAL_DETAILS_DOC_DATA['documentType'])
    self.assertIsNotNone(document.get('id'))

    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    lot_id = response.json['data']['id']
    doc_id = document['id']

    response = self.app.get('/{}/documents/{}'.format(lot_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['title'], PLATFORM_LEGAL_DETAILS_DOC_DATA['title'])
    self.assertEqual(response.json['data']['description'], PLATFORM_LEGAL_DETAILS_DOC_DATA['description'])
    self.assertEqual(response.json['data']['url'], PLATFORM_LEGAL_DETAILS_DOC_DATA['url'])
    self.assertEqual(response.json['data']['documentOf'], PLATFORM_LEGAL_DETAILS_DOC_DATA['documentOf'])
    self.assertEqual(response.json['data']['documentType'], PLATFORM_LEGAL_DETAILS_DOC_DATA['documentType'])

    check_patch_status_200(self, '/{}'.format(lot_id), 'composing', access_header)

    response = self.app.patch_json(
        '/{}/documents/{}'.format(lot_id, doc_id),
        params={'data': {'title': 'another'}},
        headers=access_header
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['title'], 'another')
