# -*- coding: utf-8 -*-
import os
from copy import deepcopy
from uuid import uuid4

from openregistry.lots.core.tests.base import (
    BaseLotWebTest as BaseLWT
)
from openregistry.lots.loki.utils import get_now
from openregistry.lots.loki.tests.json_data import (
    test_loki_lot_data,
    auction_english_data,
    auction_second_english_data
)


def add_decisions(self, lot):
    asset_decision = {
            'decisionDate': get_now().isoformat(),
            'decisionID': 'decisionAssetID',
            'decisionOf': 'asset'
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
    self.assertEqual(response.json['data']['decisions'], data_with_decisions['decisions'])


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
    data['decisions'][0]['relatedItem'] = '1' * 32
    response = self.app.post_json('/', {"data": data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], 'draft')
    self.assertEqual(response.json['data']['decisions'][0]['decisionOf'], 'lot')
    self.assertNotIn('relatedItem', response.json['data']['decisions'][0])
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


class BaseLotWebTest(BaseLWT):
    initial_auth = ('Basic', ('broker', ''))
    relative_to = os.path.dirname(__file__)

    def setUp(self):
        self.initial_data = deepcopy(test_loki_lot_data)
        self.initial_data['assets'] = [uuid4().hex]
        super(BaseLotWebTest, self).setUp()


class LotContentWebTest(BaseLotWebTest):
    init = True
    initial_status = 'pending'
