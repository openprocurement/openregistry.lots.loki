# -*- coding: utf-8 -*-
from copy import deepcopy

from openregistry.lots.core.utils import get_now
from openregistry.lots.loki.tests.base import (
    add_lot_decision,
    add_auctions,
    add_decisions,
    check_patch_status_200
)


def create_decision(self):
    self.app.authorization = ('Basic', ('broker', ''))

    decision_data = deepcopy(self.initial_decision_data)

    response = self.app.get('/{}'.format(self.resource_id))
    old_decs_count = len(response.json['data'].get('decisions', []))

    decision_data.update({
        'relatedItem': '1' * 32,
        'decisionOf': 'asset'
    })
    response = self.app.post_json(
        '/{}/decisions'.format(self.resource_id),
        {"data": decision_data},
        headers=self.access_header
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.json['data']['decisionDate'], decision_data['decisionDate'])
    self.assertEqual(response.json['data']['decisionID'], decision_data['decisionID'])
    self.assertEqual(response.json['data']['decisionOf'], 'lot')
    self.assertNotIn('relatedItem', response.json['data'])

    response = self.app.get('/{}'.format(self.resource_id))
    present_decs_count = len(response.json['data'].get('decisions', []))
    self.assertEqual(old_decs_count + 1, present_decs_count)


def patch_decision(self):
    self.app.authorization = ('Basic', ('broker', ''))
    self.initial_status = 'draft'
    self.create_resource()

    check_patch_status_200(self, '/{}'.format(self.resource_id), 'composing', self.access_header)
    lot = add_lot_decision(self, self.resource_id, self.access_header)
    add_auctions(self, lot, self.access_header)
    check_patch_status_200(self, '/{}'.format(self.resource_id), 'verification', self.access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(self.resource_id), 'pending')

    self.app.authorization = ('Basic', ('broker', ''))
    decisions = self.app.get('/{}/decisions'.format(self.resource_id)).json['data']
    asset_decision_id = filter(lambda d: d['decisionOf'] == 'asset', decisions)[0]['id']
    lot_decision_id = filter(lambda d: d['decisionOf'] == 'lot', decisions)[0]['id']

    decision_data = {'title': 'Some Title'}
    response = self.app.patch_json(
        '/{}/decisions/{}'.format(self.resource_id, asset_decision_id),
        params={'data': decision_data},
        status=403,
        headers=self.access_header
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'Can edit only decisions which have decisionOf equal to \'lot\'.'
    )

    response = self.app.patch_json(
        '/{}/decisions/{}'.format(self.resource_id, lot_decision_id),
        params={'data': decision_data},
        headers=self.access_header
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['id'], lot_decision_id)
    self.assertEqual(response.json['data']['title'], decision_data['title'])


def patch_decisions_with_lot_by_concierge(self):
    self.app.authorization = ('Basic', ('broker', ''))
    self.initial_status = 'draft'
    self.create_resource()

    decision_data = [
        {
            'decisionID': 'decID',
            'decisionDate': get_now().isoformat(),
            'relatedItem': '1' * 32,
            'decisionOf': 'asset'
        }
    ]
    decision_data = {
        'decisions': decision_data
    }

    check_patch_status_200(self, '/{}'.format(self.resource_id), 'composing', self.access_header)
    lot = add_lot_decision(self, self.resource_id, self.access_header)
    add_auctions(self, lot, self.access_header)
    check_patch_status_200(self, '/{}'.format(self.resource_id), 'verification', self.access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    response = self.app.patch_json(
        '/{}'.format(self.resource_id),
        params={'data': decision_data},
        headers=self.access_header
    )
    decision = response.json['data']['decisions'][0]
    self.assertEqual(decision['decisionID'], decision_data['decisions'][0]['decisionID'])
    self.assertEqual(decision['decisionDate'], decision_data['decisions'][0]['decisionDate'])
    self.assertEqual(decision['relatedItem'], decision_data['decisions'][0]['relatedItem'])
    self.assertEqual(decision['decisionOf'], decision_data['decisions'][0]['decisionOf'])
    decision_id = decision['id']

    response = self.app.get('/{}/decisions/{}'.format(self.resource_id, decision_id))
    self.assertEqual(response.json['data']['id'], decision_id)
    self.assertEqual(response.json['data']['decisionID'], decision_data['decisions'][0]['decisionID'])
    self.assertEqual(response.json['data']['decisionDate'], decision_data['decisions'][0]['decisionDate'])
    self.assertEqual(response.json['data']['relatedItem'], decision_data['decisions'][0]['relatedItem'])
    self.assertEqual(response.json['data']['decisionOf'], decision_data['decisions'][0]['decisionOf'])


def patch_decisions_with_lot_by_broker(self):
    self.app.authorization = ('Basic', ('broker', ''))
    self.initial_status = 'draft'
    self.create_resource()

    decision_data = [
        {
            'decisionID': 'decID',
            'decisionDate': get_now().isoformat()
        },
        {
            'decisionID': 'decID2',
            'decisionDate': get_now().isoformat()
        }
    ]
    decision_data = {
        'decisions': decision_data
    }

    check_patch_status_200(self, '/{}'.format(self.resource_id), 'composing', self.access_header)
    response = self.app.patch_json(
        '/{}'.format(self.resource_id),
        params={'data': decision_data},
        headers=self.access_header
    )
    self.assertNotIn('decisions', response.json)