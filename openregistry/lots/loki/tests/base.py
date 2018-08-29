# -*- coding: utf-8 -*-
import os
from copy import deepcopy
from uuid import uuid4

from openregistry.lots.loki.utils import get_now
from openregistry.lots.core.constants import (
    SANDBOX_MODE,
)
from openregistry.lots.loki.tests.fixtures import PARTIAL_MOCK_CONFIG
from openregistry.lots.core.tests.base import (
    connection_mock_config,
    BaseLotWebTest as BaseLWT,
    MOCK_CONFIG as BASE_MOCK_CONFIG
)
from openregistry.lots.loki.tests.json_data import (
    test_loki_lot_data,
    auction_english_data,
    auction_second_english_data,
    test_loki_item_data
)

DEFAULT_ACCELERATION = 1440


if SANDBOX_MODE:
    test_loki_lot_data['sandboxParameters'] = 'quick, accelerator={}'.format(DEFAULT_ACCELERATION)


def add_decisions(self, lot):
    asset_decision = {
            'decisionDate': get_now().isoformat(),
            'decisionID': 'decisionAssetID',
            'decisionOf': 'asset',
            'relatedItem': '1' * 32
        }
    data_with_decisions = {
        "decisions": [
            lot['decisions'][0], asset_decision
        ]
    }
    response = self.app.patch_json('/{}'.format(lot['id']), params={'data': data_with_decisions})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['decisions'][0]['decisionOf'], 'lot')
    self.assertEqual(response.json['data']['decisions'][0]['id'], data_with_decisions['decisions'][0]['id'])
    self.assertEqual(response.json['data']['decisions'][0]['decisionID'], data_with_decisions['decisions'][0]['decisionID'])
    self.assertNotIn('relatedItem', response.json['data']['decisions'][0])

    self.assertEqual(response.json['data']['decisions'][1]['decisionOf'], 'asset')
    self.assertIsNotNone(response.json['data']['decisions'][1].get('id'))
    self.assertEqual(
        response.json['data']['decisions'][1]['decisionID'],
        data_with_decisions['decisions'][1]['decisionID']
    )
    self.assertEqual(
        response.json['data']['decisions'][1]['relatedItem'],
        data_with_decisions['decisions'][1]['relatedItem']
    )


def add_auctions(self, lot, access_header):
    response = self.app.get('/{}/auctions'.format(lot['id']))
    auctions = sorted(response.json['data'], key=lambda a: a['tenderAttempts'])
    english = auctions[0]
    second_english = auctions[1]

    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], english['id']),
        params={'data': auction_english_data}, headers=access_header)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], second_english['id']),
        params={'data': auction_second_english_data}, headers=access_header)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')


def check_patch_status_200(self, path, lot_status, headers=None, extra={}):
    data = {'status': lot_status}
    data.update(extra)
    response = self.app.patch_json(path,
                                   headers=headers,
                                   params={'data': data})
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
    self.assertNotIn('decisions', response.json['data'])
    self.assertEqual(len(response.json['data']['auctions']), 3)
    token = response.json['access']['token']
    lot_id = response.json['data']['id']

    if status:
        access_header = {'X-Access-Token': str(token)}
        add_auctions(self, response.json['data'], access_header)
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


def add_lot_decision(self, lot_id, headers):
    old_authorization = self.app.authorization
    self.app.authorization = ('Basic', ('broker', ''))

    response = self.app.get('/{}'.format(lot_id))
    old_decs_count = len(response.json['data'].get('decisions', []))

    decision_data = {
        'decisionDate': get_now().isoformat(),
        'decisionID': 'decisionLotID'
    }
    response = self.app.post_json(
        '/{}/decisions'.format(lot_id),
        {"data": decision_data},
        headers=headers
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.json['data']['decisionDate'], decision_data['decisionDate'])
    self.assertEqual(response.json['data']['decisionID'], decision_data['decisionID'])

    response = self.app.get('/{}'.format(lot_id))
    present_decs_count = len(response.json['data'].get('decisions', []))
    self.assertEqual(old_decs_count + 1, present_decs_count)

    self.app.authorization = old_authorization
    return response.json['data']


def add_lot_related_process(self, lot_id, headers):
    old_authorization = self.app.authorization
    self.app.authorization = ('Basic', ('broker', ''))

    response = self.app.get('/{}'.format(lot_id))
    old_related_processes = len(response.json['data'].get('relatedProcesses', []))

    rP_data = {
        'relatedProcessID': uuid4().hex,
    }
    response = self.app.post_json(
        '/{}/related_processes'.format(lot_id),
        {"data": rP_data},
        headers=headers
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.json['data']['relatedProcessID'], rP_data['relatedProcessID'])

    response = self.app.get('/{}'.format(lot_id))
    present_related_processes = len(response.json['data'].get('relatedProcesses', []))
    self.assertEqual(old_related_processes + 1, present_related_processes)

    self.app.authorization = old_authorization
    return response.json['data']


MOCK_CONFIG = connection_mock_config(PARTIAL_MOCK_CONFIG,
                                     base=BASE_MOCK_CONFIG,
                                     connector=('plugins', 'api', 'plugins',
                                                'lots.core', 'plugins'))


class BaseLotWebTest(BaseLWT):
    initial_auth = ('Basic', ('broker', ''))
    relative_to = os.path.dirname(__file__)
    mock_config = MOCK_CONFIG

    def setUp(self):
        self.initial_data = deepcopy(test_loki_lot_data)
        super(BaseLotWebTest, self).setUp()


class LotContentWebTest(BaseLotWebTest):
    init = True
    initial_status = 'pending'
    mock_config = MOCK_CONFIG
