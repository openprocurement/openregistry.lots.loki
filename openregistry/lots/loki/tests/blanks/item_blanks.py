# -*- coding: utf-8 -*-
from datetime import timedelta

from openregistry.lots.core.utils import (
    get_now,
    calculate_business_date
)
from openregistry.lots.core.models import Period
from openregistry.lots.loki.models import Lot


def create_item_resource(self):
    response = self.app.post_json('/{}/items'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_item_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    item_id = response.json["data"]['id']
    self.assertIn(item_id, response.headers['Location'])
    self.assertEqual(self.initial_item_data['description'], response.json["data"]["description"])
    self.assertEqual(self.initial_item_data['quantity'], response.json["data"]["quantity"])
    self.assertEqual(self.initial_item_data['address'], response.json["data"]["address"])


def patch_item(self):
    response = self.app.post_json('/{}/items'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_item_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    item_id = response.json["data"]['id']
    self.assertIn(item_id, response.headers['Location'])
    self.assertEqual(self.initial_item_data['description'], response.json["data"]["description"])
    self.assertEqual(self.initial_item_data['quantity'], response.json["data"]["quantity"])
    self.assertEqual(self.initial_item_data['address'], response.json["data"]["address"])

    response = self.app.patch_json('/{}/items/{}'.format(self.resource_id, item_id),
        headers=self.access_header, params={
            "data": {
                "description": "new item description",
                "registrationDetails": self.initial_item_data['registrationDetails'],
                "unit": self.initial_item_data['unit'],
                "address": self.initial_item_data['address'],
                "quantity": self.initial_item_data['quantity'],
                "classification": self.initial_item_data['classification'],
            }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(item_id, response.json["data"]["id"])
    self.assertEqual(response.json["data"]["description"], 'new item description')


def create_item_resource_invalid(self):
    pass


def patch_item_resource_invalid(self):
    pass


def list_item_resource(self):
    pass


def rectificationPeriod_item_workflow(self):
    rectificationPeriod = Period()
    rectificationPeriod.startDate = get_now() - timedelta(3)
    rectificationPeriod.endDate = calculate_business_date(rectificationPeriod.startDate,
                                                          timedelta(1),
                                                          None)

    lot = self.create_resource()

    response = self.app.post_json('/{}/items'.format(lot['id']),
                                  headers=self.access_header,
                                  params={'data': self.initial_item_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    item_id = response.json["data"]['id']
    self.assertIn(item_id, response.headers['Location'])
    self.assertEqual(self.initial_item_data['description'], response.json["data"]["description"])
    self.assertEqual(self.initial_item_data['quantity'], response.json["data"]["quantity"])
    self.assertEqual(self.initial_item_data['address'], response.json["data"]["address"])
    item_id = response.json['data']['id']

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

    response = self.app.post_json('/{}/items'.format(lot['id']),
                                   headers=self.access_header,
                                   params={'data': self.initial_item_data},
                                   status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]['description'], 'You can\'t change items after rectification period')


    self.assertEqual(response.json['errors'][0]['description'], 'You can\'t change items after rectification period')
    response = self.app.patch_json('/{}/items/{}'.format(lot['id'], item_id),
                                   headers=self.access_header,
                                   params={'data': self.initial_item_data},
                                   status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]['description'], 'You can\'t change items after rectification period')


