 # -*- coding: utf-8 -*-
import unittest

from copy import deepcopy
from uuid import uuid4
from datetime import timedelta

from openregistry.lots.core.utils import get_now, calculate_business_date
from openregistry.lots.core.models import Period
from openregistry.lots.core.constants import ROUTE_PREFIX, SANDBOX_MODE
from openregistry.lots.core.tests.base import create_blacklist

from openregistry.lots.loki.models import Lot
from openregistry.lots.loki.constants import (
    STATUS_CHANGES,
    LOT_STATUSES,
    DEFAULT_DUTCH_STEPS
)


ROLES = ['lot_owner', 'Administrator', 'concierge', 'convoy']
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


def add_decisions(self, lot):
    asset_decision = {
            'decisionDate': get_now().isoformat(),
            'decisionID': 'decisionAssetID'
        }
    data_with_decisions = {
        "decisions": [
            lot['decisions'][0],
            asset_decision
        ]
    }
    response = self.app.patch_json('/{}'.format(lot['id']), params={'data': data_with_decisions})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['decisions'], data_with_decisions['decisions'])


def check_patch_status_200(self, path, lot_status, headers=None):
    response = self.app.patch_json(path,
                                   headers=headers,
                                   params={'data': {'status': lot_status}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], lot_status)


def check_patch_status_403(self, path, lot_status, headers=None):

    # Check if response.status is forbidden, when you try to change status to incorrect
    # 'data' should be {'data': {'status': allowed_status}}
    response = self.app.patch_json(path,
                                   params={'data': {'status': lot_status}},
                                   headers=headers,
                                   status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')


def create_single_lot(self, data, status=None):
    response = self.app.post_json('/', {"data": data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], 'draft')
    token = response.json['access']['token']
    lot_id = response.json['data']['id']

    if status:
        fromdb = self.db.get(lot_id)
        fromdb = self.lot_model(fromdb)

        fromdb.status = status
        fromdb.store(self.db)

        response = self.app.get('/{}'.format(lot_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['id'], lot_id)
        self.assertEqual(response.json['data']['status'], status)
        new_json = deepcopy(response.json)
        new_json['access'] = {'token': token}
        return new_json

    return response


@unittest.skipIf(not SANDBOX_MODE, 'If sandbox mode is enabled auctionParameters has additional field procurementMethodDetails')
def procurementMethodDetails_check_with_sandbox(self):
    data = deepcopy(self.initial_data)
    data['auctions'][0]['auctionParameters'] = {'procurementMethodDetails': 'quick'}
    response = create_single_lot(self, data)
    self.assertEqual(
        response.json['data']['auctions'][0]['auctionParameters']['procurementMethodDetails'],
        data['auctions'][0]['auctionParameters']['procurementMethodDetails']
    )
    self.assertEqual(
        response.json['data']['auctions'][1]['auctionParameters']['procurementMethodDetails'],
        data['auctions'][0]['auctionParameters']['procurementMethodDetails']
    )
    self.assertEqual(
        response.json['data']['auctions'][2]['auctionParameters']['procurementMethodDetails'],
        data['auctions'][0]['auctionParameters']['procurementMethodDetails']
    )


@unittest.skipIf(SANDBOX_MODE, 'If sandbox mode is disabled auctionParameters has not procurementMethodDetails field')
def procurementMethodDetails_check_without_sandbox(self):
    data = deepcopy(self.initial_data)
    data['auctions'][0]['auctionParameters'] = {'procurementMethodDetails': 'quick'}
    response = self.app.post_json('/', {"data": data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description']['auctionParameters']['procurementMethodDetails'], u'Rogue field')

    response = create_single_lot(self, self.initial_data)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        params={'data': data},
        headers=access_header,
        status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description']['auctionParameters']['procurementMethodDetails'], u'Rogue field')


def check_lotIdentifier(self):
    data = deepcopy(self.initial_data)
    data['lotIdentifier'] = ''
    response = self.app.post_json('/', {"data": data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'], ["String value is too short."])

    del data['lotIdentifier']
    response = self.app.post_json('/', {"data": data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'], ["This field is required."])

    data['lotIdentifier'] = 'Q24421K222'
    lot = create_single_lot(self, data).json['data']
    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(set(response.json['data']), set(lot))
    self.assertEqual(response.json['data'], lot)


def check_auctions(self):
    self.app.authorization = ('Basic', ('broker', ''))
    data = deepcopy(self.initial_data)
    data['auctions'][0]['tenderingDuration'] = 'P25DT12H'

    response = self.app.post_json('/', {"data": data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'], ["First loki.english have no tenderingDuration."])

    del data['auctions'][0]['tenderingDuration']
    data['auctions'][1]['tenderingDuration'] = 'P30DT12H'

    response = self.app.post_json('/', {"data": data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'], ["tenderingDuration for second loki.english and loki.insider should be the same."])

    duration = data['auctions'][2]['tenderingDuration']

    # Delete tenderingDuration in second loki.english
    del data['auctions'][1]['tenderingDuration']
    response = self.app.post_json('/', {"data": data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'], ["tenderingDuration is required for second loki.english and loki.insider."])

    # Delete tenderingDuration in both second loki.english and loki.insider
    del data['auctions'][2]['tenderingDuration']
    response = self.app.post_json('/', {"data": data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'], ["tenderingDuration is required for second loki.english and loki.insider."])

    # Delete tenderingDuration in loki.insider
    data['auctions'][1]['tenderingDuration'] = duration
    response = self.app.post_json('/', {"data": data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'], ["tenderingDuration is required for second loki.english and loki.insider."])

    response = create_single_lot(self, self.initial_data)
    lot = response.json['data']
    self.assertEqual(len(lot['auctions']), 3)

    # Test first Loki.english
    self.assertEqual(lot['auctions'][0]['procurementMethodType'], 'Loki.english')
    self.assertEqual(lot['auctions'][0]['value']['amount'], self.initial_data['auctions'][0]['value']['amount'])
    self.assertEqual(lot['auctions'][0]['registrationFee']['amount'], self.initial_data['auctions'][0]['registrationFee']['amount'])
    self.assertEqual(lot['auctions'][0]['minimalStep']['amount'], self.initial_data['auctions'][0]['minimalStep']['amount'])
    self.assertEqual(lot['auctions'][0]['guarantee']['amount'], lot['auctions'][0]['guarantee']['amount'])
    self.assertEqual(lot['auctions'][0]['auctionParameters']['type'], 'english')
    self.assertNotIn('dutchSteps', lot['auctions'][0]['auctionParameters'])
    self.assertNotIn('tenderingDuration', lot['auctions'][0])

    # Test second Loki.english(half values)
    self.assertEqual(lot['auctions'][1]['procurementMethodType'], 'Loki.english')
    self.assertEqual(lot['auctions'][1]['value']['amount'], lot['auctions'][0]['value']['amount'] / 2)
    self.assertEqual(lot['auctions'][1]['registrationFee']['amount'], lot['auctions'][0]['registrationFee']['amount'] / 2)
    self.assertEqual(lot['auctions'][1]['minimalStep']['amount'], lot['auctions'][0]['minimalStep']['amount'] / 2)
    self.assertEqual(lot['auctions'][1]['guarantee']['amount'], lot['auctions'][0]['guarantee']['amount'] / 2)
    self.assertEqual(lot['auctions'][1]['auctionParameters']['type'], 'english')
    self.assertNotIn('dutchSteps', lot['auctions'][1]['auctionParameters'])

    # Test second Loki.insider(half values)
    self.assertEqual(lot['auctions'][2]['procurementMethodType'], 'Loki.insider')
    self.assertEqual(lot['auctions'][2]['value']['amount'], lot['auctions'][0]['value']['amount'] / 2)
    self.assertEqual(lot['auctions'][2]['registrationFee']['amount'], lot['auctions'][0]['registrationFee']['amount'] / 2)
    self.assertEqual(lot['auctions'][2]['minimalStep']['amount'], lot['auctions'][0]['minimalStep']['amount'] / 2)
    self.assertEqual(lot['auctions'][2]['guarantee']['amount'], lot['auctions'][0]['guarantee']['amount'] / 2)
    self.assertEqual(lot['auctions'][2]['auctionParameters']['type'], 'insider')
    self.assertEqual(lot['auctions'][2]['auctionParameters']['dutchSteps'], DEFAULT_DUTCH_STEPS)

    # Test dutch steps validation
    data = deepcopy(self.initial_data)
    data['auctions'][0]['auctionParameters'] = {'dutchSteps': 66}
    response = self.app.post_json('/', {"data": data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'], ["dutchSteps can be filled only when procurementMethodType is Loki.insider."])

    data = deepcopy(self.initial_data)
    data['auctions'][1]['auctionParameters'] = {'dutchSteps': 66}
    response = self.app.post_json('/', {"data": data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'], ["dutchSteps can be filled only when procurementMethodType is Loki.insider."])

    data = deepcopy(self.initial_data)
    data['auctions'][2]['auctionParameters'] = {'dutchSteps': 66}
    response = create_single_lot(self, data)
    lot = response.json['data']
    self.assertEqual(len(lot['auctions']), 3)

    self.assertEqual(lot['auctions'][2]['auctionParameters']['dutchSteps'], data['auctions'][2]['auctionParameters']['dutchSteps'])


def check_decisions(self):
    self.app.authorization = ('Basic', ('broker', ''))

    data_with_two_decisions = deepcopy(self.initial_data)
    data_with_two_decisions['decisions'].append({
        'decisionDate': get_now().isoformat(),
        'decisionID': 'secondDecisionID'
    })
    response = self.app.post_json(
        '/',
        params={'data': data_with_two_decisions},
        status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'Can\'t add more than one decisions to lot'
    )

    response = create_single_lot(self, self.initial_data)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
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

    asset_decision = {
            'decisionDate': get_now().isoformat(),
            'decisionID': 'decisionAssetID'
        }
    data_with_decisions = {
        "decisions": [
            lot['decisions'][0],
            asset_decision
        ],
        'status': 'pending'
    }
    response = self.app.patch_json('/{}'.format(lot['id']), params={'data': data_with_decisions})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], 'pending')
    self.assertEqual(response.json['data']['decisions'], data_with_decisions['decisions'])

    self.app.authorization = ('Basic', ('broker', ''))
    lot_data_with_decisions = {
        "decisions": [{
            'decisionDate': get_now().isoformat(),
            'decisionID': 'decisionLotID'
        }, {
            'decisionDate': get_now().isoformat(),
            'decisionID': 'wrong'
        }
        ]
    }

    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        headers=access_header,
        params={'data': lot_data_with_decisions},
        status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'Can\'t update decision that was created from asset'
    )

    lot_data_with_decisions = {
        "decisions": []
    }

    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        headers=access_header,
        params={'data': lot_data_with_decisions},
        status=[200, 403]
    )

    lot_data_with_decisions = {
        "decisions": deepcopy(data_with_decisions['decisions'])
    }
    del lot_data_with_decisions['decisions'][1]
    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        headers=access_header,
        params={'data': lot_data_with_decisions},
        status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'Can\'t update decision that was created from asset'
    )

    lot_data_with_decisions['decisions'] = deepcopy(data_with_decisions['decisions'])
    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        headers=access_header,
        params={'data': lot_data_with_decisions},
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['decisions'], lot_data_with_decisions['decisions'])


def rectificationPeriod_workflow(self):
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

    response = self.app.patch_json('/{}'.format(lot['id']),
                                   headers=access_header,
                                   params={'data': {'title': ' PATCHED'}})
    self.assertNotEqual(response.json['data']['title'], 'PATCHED')
    self.assertEqual(lot['title'], response.json['data']['title'])

    add_cancellationDetails_document(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'deleted', access_header)


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
    data['lotIdentifier'] = 'Q24421K222'
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
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)


    self.app.authorization = ('Basic', ('concierge', ''))
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending')

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

    # Move from 'verification' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['composing']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)


    self.app.authorization = ('Basic', ('convoy', ''))
    for status in STATUS_BLACKLIST['composing']['convoy']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['composing']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'draft' to 'composing' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)

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
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    # Move from 'verification' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['verification']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)


    self.app.authorization = ('Basic', ('convoy', ''))
    # Move from 'verification' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['verification']['convoy']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    # Move from 'verification' to 'pending' status
    self.app.authorization = ('Basic', ('concierge', ''))
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending')


    self.app.authorization = ('Basic', ('broker', ''))
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
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
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    # Move from 'verification' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['verification']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))
    # Move from 'verification' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['verification']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


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
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)


    self.app.authorization = ('Basic', ('concierge', ''))

    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification')
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending')

    self.app.authorization = ('Basic', ('broker', ''))

    # Move from 'pending' to 'pending' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', access_header)

    # Move status from Pending to Deleted 403
    response = self.app.patch_json('/{}'.format(lot['id']),
                                   headers=access_header,
                                   params={'data': {'status': 'deleted'}},
                                   status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'],
                    u"You can set deleted status"
                    u"only when asset have at least one document with \'cancellationDetails\' documentType")


    # Move from 'pending' to 'deleted' status
    add_cancellationDetails_document(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'deleted', access_header)

    # Create lot in 'draft' status and move it to 'pending'
    response = create_single_lot(self, deepcopy(lot_info))
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    lot = response.json['data']

    # Move from 'draft' to 'composing' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)


    self.app.authorization = ('Basic', ('concierge', ''))
    # Move from 'verification' to 'pending' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification')
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending')


    self.app.authorization = ('Basic', ('broker', ''))

    # Move from 'pending' to 'active.salable' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.salable', access_header)

    # Create lot in 'draft' status and move it to 'pending'
    response = create_single_lot(self, deepcopy(lot_info))
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    lot = response.json['data']

    # Move from 'draft' to 'composing' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    # Move from 'composing' to 'pending' status
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending')


    # Move from 'pending' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['pending']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)


    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'pending' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['pending']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('convoy', ''))

    # Move from 'pending' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['pending']['convoy']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'pending' to 'pending' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending')

    # Move from 'pending' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['pending']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    # Move status from Pending to Deleted 403
    response = self.app.patch_json('/{}'.format(lot['id']),
                                   params={'data': {'status': 'deleted'}},
                                   status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'],
                    u"You can set deleted status"
                    u"only when asset have at least one document with \'cancellationDetails\' documentType")


    # Move from 'pending' to 'deleted'
    self.app.authorization = ('Basic', ('broker', ''))
    add_cancellationDetails_document(self, lot, access_header)
    self.app.authorization = ('Basic', ('administrator', ''))

    check_patch_status_200(self, '/{}'.format(lot['id']), 'deleted')


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
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)


    self.app.authorization = ('Basic', ('concierge', ''))
    # Move from 'composing' to 'pending' status
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending')


    self.app.authorization = ('Basic', ('broker', ''))

    # Move from 'pending' to 'deleted'
    add_cancellationDetails_document(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'deleted', access_header)

    # Move from 'deleted' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['deleted']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)


    self.app.authorization = ('Basic', ('convoy', ''))

    # Move from 'deleted' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['deleted']['convoy']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'deleted' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['deleted']['concierge']:
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

    self.app.authorization = ('Basic', ('convoy', ''))

    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.awaiting')
    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.salable')

    # Move from 'active.salable' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['active.salable']['convoy']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))

    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.awaiting')
    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.salable')

    # Move from 'active.salable' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['active.salable']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)



def change_active_awaiting_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)


    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'active.awaiting' status
    json = create_single_lot(self, lot_info, 'active.awaiting')
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'active.awaiting')


    # Move from 'active.awaiting' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('broker', ''))
    for status in STATUS_BLACKLIST['active.awaiting']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'active.awaiting' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['active.awaiting']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('convoy', ''))

    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.salable')
    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.awaiting')
    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.auction')

    # Create new lot in 'active.awaiting' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.awaiting')
    lot = json['data']
    token = json['access']['token']
    self.assertEqual(lot['status'], 'active.awaiting')

    # Move from 'active.awaiting' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('convoy', ''))
    for status in STATUS_BLACKLIST['active.awaiting']['convoy']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))

    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.salable')
    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.awaiting')
    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.auction')

    # Create new lot in 'active.awaiting' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.awaiting')
    lot = json['data']
    token = json['access']['token']
    self.assertEqual(lot['status'], 'active.awaiting')

    # Move from 'active.awaiting' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('administrator', ''))
    for status in STATUS_BLACKLIST['active.awaiting']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


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


    self.app.authorization = ('Basic', ('convoy', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.contracting')


    # Create new lot in 'active.auction' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.auction')
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'active.auction')


    self.app.authorization = ('Basic', ('convoy', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.dissolution')


    # Create new lot in 'active.auction' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.auction')
    lot = json['data']
    token = json['access']['token']
    self.assertEqual(lot['status'], 'active.auction')

    # Move from 'active.auction' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('convoy', ''))
    for status in STATUS_BLACKLIST['active.auction']['convoy']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))
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


    self.app.authorization = ('Basic', ('convoy', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.sold')


    # Create new lot in 'active.contracting' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.contracting')
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'active.contracting')


    self.app.authorization = ('Basic', ('convoy', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.dissolution')


    # Create new lot in 'active.contracting' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'active.contracting')
    lot = json['data']
    token = json['access']['token']
    self.assertEqual(lot['status'], 'active.contracting')

    # Move from 'active.contracting' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('convoy', ''))
    for status in STATUS_BLACKLIST['active.contracting']['convoy']:
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


    # Move from 'pending.sold' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('convoy', ''))
    for status in STATUS_BLACKLIST['pending.sold']['convoy']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'sold')


    # Create new lot in 'pending.sold' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info, 'pending.sold')
    lot = json['data']
    token = json['access']['token']
    self.assertEqual(lot['status'], 'pending.sold')

    # Move from 'pending.sold' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('convoy', ''))
    for status in STATUS_BLACKLIST['pending.sold']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


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


    # Move from 'pending.dissolution' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('convoy', ''))
    for status in STATUS_BLACKLIST['pending.dissolution']['convoy']:
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


    self.app.authorization = ('Basic', ('convoy', ''))

    # Move from 'sold' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['sold']['convoy']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'sold' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['sold']['concierge']:
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
    for status in STATUS_BLACKLIST['sold']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)


    self.app.authorization = ('Basic', ('convoy', ''))

    # Move from 'dissolved' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['sold']['convoy']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'dissolved' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['sold']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'dissolved' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['sold']['Administrator']:
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


    self.app.authorization = ('Basic', ('convoy', ''))

    # Move from 'invalid' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['invalid']['convoy']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'invalid' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['invalid']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'invalid' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['invalid']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)
