# -*- coding: utf-8 -*-
from datetime import timedelta
from copy import deepcopy

from openregistry.lots.core.utils import (
    get_now,
    calculate_business_date
)

from openregistry.lots.loki.models import (
    Lot,
    Period
)
from openregistry.lots.loki.tests.json_data import test_loki_item_data
from openregistry.lots.loki.tests.base import (
    add_lot_decision,
    add_auctions,
    add_decisions,
    check_patch_status_200,
    add_lot_related_process
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
    add_lot_decision(self, self.resource_id, self.access_header)
    lot = add_lot_related_process(self, self.resource_id, self.access_header)
    add_auctions(self, lot, self.access_header)
    check_patch_status_200(self, '/{}'.format(self.resource_id), 'verification', self.access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(self.resource_id), 'pending', extra={'items': [test_loki_item_data]})

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
    add_lot_decision(self, self.resource_id, self.access_header)
    lot = add_lot_related_process(self, self.resource_id, self.access_header)
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


def create_or_patch_decision_in_not_allowed_status(self):
    self.app.authorization = ('Basic', ('broker', ''))
    self.initial_status = 'draft'
    self.create_resource()

    check_patch_status_200(self, '/{}'.format(self.resource_id), 'composing', self.access_header)
    lot = add_lot_decision(self, self.resource_id, self.access_header)
    add_lot_related_process(self, self.resource_id, self.access_header)
    add_auctions(self, lot, self.access_header)
    check_patch_status_200(self, '/{}'.format(self.resource_id), 'verification', self.access_header)

    decision_data = {
        'decisionDate': get_now().isoformat(),
        'decisionID': 'decisionLotID'
    }
    response = self.app.post_json(
        '/{}/decisions'.format(self.resource_id),
        {"data": decision_data},
        headers=self.access_header,
        status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'Can\'t update decisions in current (verification) lot status'
    )


def rectificationPeriod_decision_workflow(self):
    rectificationPeriod = Period()
    rectificationPeriod.startDate = get_now() - timedelta(3)
    rectificationPeriod.endDate = calculate_business_date(rectificationPeriod.startDate,
                                                          timedelta(1),
                                                          None)

    self.create_resource()
    response = self.app.get('/{}'.format(self.resource_id))
    lot = response.json['data']

    self.set_status('draft')
    add_auctions(self, lot, access_header=self.access_header)
    self.set_status('pending')
    add_lot_decision(self, lot['id'], self.access_header)

    response = self.app.post_json('/{}/decisions'.format(lot['id']),
                                  headers=self.access_header,
                                  params={'data': self.initial_decision_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    decision_id = response.json["data"]['id']
    self.assertIn(decision_id, response.headers['Location'])
    self.assertEqual(self.initial_decision_data['decisionID'], response.json["data"]["decisionID"])
    self.assertEqual(self.initial_decision_data['decisionDate'], response.json["data"]["decisionDate"])
    self.assertEqual('lot', response.json["data"]["decisionOf"])
    decision_id = response.json['data']['id']

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['id'], lot['id'])

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

    response = self.app.post_json('/{}/decisions'.format(lot['id']),
                                   headers=self.access_header,
                                   params={'data': self.initial_decision_data},
                                   status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]['description'], 'You can\'t change or add decisions after rectification period')

    response = self.app.patch_json('/{}/decisions/{}'.format(lot['id'], decision_id),
                                   headers=self.access_header,
                                   params={'data': self.initial_decision_data},
                                   status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]['description'], 'You can\'t change or add decisions after rectification period')


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


def create_decisions_with_lot(self):
    data = deepcopy(self.initial_data)
    decision_1 = {'id': '1' * 32,  'decisionID': 'decID',  'decisionDate': get_now().isoformat()}
    decision_2 = deepcopy(decision_1)
    decision_2['id'] = '2' * 32
    data['decisions'] = [
       decision_1, decision_2
    ]
    response = self.app.post_json('/', params={'data': data})
    decision_1['decisionOf'] = 'lot'
    decision_2['decisionOf'] = 'lot'
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(len(response.json['data']['decisions']), 2)
    self.assertEqual(response.json['data']['decisions'][0], decision_1)
    self.assertEqual(response.json['data']['decisions'][1], decision_2)

    del decision_1['decisionOf']
    del decision_2['decisionOf']

    decision_2['id'] = '1' * 32
    data['decisions'] = [
       decision_1, decision_2
    ]
    response = self.app.post_json('/', params={'data': data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(
        response.json['errors'][0]['description'][0],
        u'Decision id should be unique for all decisions'
    )
