# -*- coding: utf-8 -*-
from datetime import timedelta
from copy import deepcopy

from openregistry.lots.core.utils import get_now, calculate_business_date
from openregistry.lots.core.models import Period
from openregistry.lots.loki.models import Lot


def not_found_item_document(self):
    response = self.app.post_json('/{}/items'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_item_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    item_id = response.json["data"]['id']


    response = self.app.post_json(
        '/some_id/items/some_id/documents', status=404,
        params={'data': self.initial_document_data}
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'lot_id'}
    ])

    response = self.app.post_json(
        '/{}/items/some_id/documents'.format(self.resource_id),
        status=404,
        params={'data': self.initial_document_data}
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'item_id'}
    ])

    response = self.app.get('/some_id/items/some_id/documents', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'lot_id'}
    ])

    response = self.app.get('/{}/items/some_id/documents'.format(self.resource_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'item_id'}
    ])

    response = self.app.get('/some_id/items/some_id/documents/some_id', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'lot_id'}
    ])

    response = self.app.get('/{}/items/some_id/documents/some_id'.format(self.resource_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'item_id'}
    ])

    response = self.app.get('/{}/items/{}/documents/some_id'.format(self.resource_id, item_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'document_id'}
    ])


    response = self.app.put_json('/some_id/items/some_id/documents/some_id', status=404,
                            upload_files=[('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'lot_id'}
    ])


    response = self.app.put_json('/{}/items/some_id/documents/some_id'.format(self.resource_id), status=404, upload_files=[
                            ('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'item_id'}
    ])

    response = self.app.put_json(
        '/{}/items/{}/documents/some_id'.format(self.resource_id, item_id),
        status=404,
        params={'data': self.initial_document_data},
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
    ])


def create_item_document(self):
    response = self.app.post_json('/{}/items'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_item_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    item_id = response.json["data"]['id']

    response = self.app.post_json('/{}/items/{}/documents'.format(
        self.resource_id, item_id),
        params={'data': self.initial_document_data},
        content_type='application/json',
        headers=self.access_header,
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual(self.initial_document_data['title'], response.json["data"]["title"])

    response = self.app.get('/{}/items/{}/documents'.format(self.resource_id, item_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"][0]["id"])
    self.assertEqual(self.initial_document_data['title'], response.json["data"][0]["title"])

    response = self.app.get('/{}/items/{}/documents?all=true'.format(self.resource_id, item_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"][0]["id"])
    self.assertEqual(self.initial_document_data['title'], response.json["data"][0]["title"])

    response = self.app.get('/{}/items/{}/documents/{}?download=some_id'.format(
        self.resource_id, item_id, doc_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
    ])

    response = self.app.get('/{}/items/{}/documents/{}'.format(
        self.resource_id, item_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual(self.initial_document_data['title'], response.json["data"]["title"])


def put_item_document(self):
    response = self.app.post_json('/{}/items'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_item_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    item_id = response.json["data"]['id']

    response = self.app.post_json('/{}/items/{}/documents'.format(
        self.resource_id, item_id),
        params={'data': self.initial_document_data},
        headers=self.access_header,
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])


    response = self.app.put_json(
        '/{}/items/{}/documents/{}'.format(self.resource_id, item_id, doc_id),
        params={'data': self.initial_document_data},
        headers=self.access_header
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])

    response = self.app.get('/{}/items/{}/documents/{}'.format(
        self.resource_id, item_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual(self.initial_document_data['title'], response.json["data"]["title"])


def patch_item_document(self):
    response = self.app.post_json('/{}/items'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_item_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    item_id = response.json["data"]['id']


    response = self.app.post_json('/{}/items/{}/documents'.format(
        self.resource_id, item_id),
        headers=self.access_header,
        params={'data': self.initial_document_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.patch_json('/{}/items/{}/documents/{}'.format(
        self.resource_id, item_id, doc_id),
        {"data": {"description": "document description"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Forbidden")

    response = self.app.patch_json(
        '/{}/items/{}/documents/{}'.format(self.resource_id, item_id, doc_id),
        {"data": {"description": "document description"}},
        headers=self.access_header
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])

    response = self.app.get('/{}/items/{}/documents/{}'.format(
        self.resource_id, item_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('document description', response.json["data"]["description"])


    response = self.app.post_json('/{}/items/{}/documents'.format(self.resource_id, item_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual(u'укр.doc', response.json["data"]["title"])
    self.assertEqual(self.initial_document_data["documentType"], response.json["data"]['documentType'])

    response = self.app.patch_json('/{}/items/{}/documents/{}'.format(self.resource_id, item_id, doc_id),
        headers=self.access_header, params={
            'data': {
                'documentOf': 'wrong_document_of',
                'relatedItem': '0' * 32
            }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u"Value must be one of ['lot', 'item']."], u'location': u'body', u'name': u'documentOf'}
    ])

    response = self.app.patch_json('/{}/items/{}/documents/{}'.format(self.resource_id, item_id, doc_id),
        headers=self.access_header, params={
            "data": {
                "description": "document description",
                "documentType": 'tenderNotice'
            }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u"Value must be one of {}.".format(str(self.document_types))], u'location': u'body', u'name': u'documentType'}
    ])
    response = self.app.patch_json('/{}/items/{}/documents/{}'.format(self.resource_id, item_id, doc_id),
        headers=self.access_header, params={
            "data": {
                "description": "document description"
            }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual(self.initial_document_data["documentType"], response.json["data"]['documentType'])

    response = self.app.get('/{}/items/{}/documents/{}'.format(self.resource_id, item_id, doc_id),
                            headers=self.access_header)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('document description', response.json["data"]["description"])
    #self.assertTrue(dateModified < response.json["data"]["dateModified"])

    for status in self.forbidden_item_document_statuses_modification:
        self.set_status(status)
        response = self.app.patch_json('/{}/items/{}/documents/{}'.format(self.resource_id, item_id, doc_id),
            headers=self.access_header, params={
                "data": {
                    "description": "document description"
                }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update document of item in current ({}) {} status".format(status, self.resource_name[:-1]))

    for status in self.forbidden_item_document_statuses_modification:
        self.set_status(status)
        response = self.app.post_json('/{}/items/{}/documents'.format(self.resource_id, item_id),
            headers=self.access_header, params={
                "data": self.initial_document_data
            }, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update document of item in current ({}) {} status".format(status, self.resource_name[:-1]))


def model_validation(self):
    response = self.app.post_json('/{}/items'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_item_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    item_id = response.json["data"]['id']


    initial_document_data = deepcopy(self.initial_document_data)
    initial_document_data['documentType'] = 'x_dgfAssetFamiliarization'
    response = self.app.post_json('/{}/items/{}/documents'.format(self.resource_id, item_id),
                                  headers=self.access_header,
                                  params={'data': initial_document_data},
                                  status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'][0], u"accessDetails is required, when documentType is x_dgfAssetFamiliarization")

    initial_document_data['accessDetails'] = u'Some access details'
    response = self.app.post_json('/{}/items/{}/documents'.format(self.resource_id, item_id),
                                  headers=self.access_header,
                                  params={'data': initial_document_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['accessDetails'], initial_document_data['accessDetails'])


def rectificationPeriod_document_workflow(self):
    rectificationPeriod = Period()
    rectificationPeriod.startDate = get_now() - timedelta(3)
    rectificationPeriod.endDate = calculate_business_date(rectificationPeriod.startDate,
                                                          timedelta(1),
                                                          None)

    lot = self.create_resource()

    response = self.app.post_json('/{}/items'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_item_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    item_id = response.json["data"]['id']

    response = self.app.post_json('/{}/items/{}/documents'.format(lot['id'], item_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']

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

    response = self.app.post_json('/{}/items/{}/documents'.format(lot['id'], item_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data},
                                  status=403
                                  )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'You can\'t add documents to item after rectification period'
    )

    response = self.app.patch_json('/{}/items/{}/documents/{}'.format(lot['id'], item_id, doc_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data},
                                  status=403
                                  )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]['description'], 'You can\'t change documents after rectification period')

    response = self.app.put_json('/{}/items/{}/documents/{}'.format(lot['id'], item_id, doc_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data},
                                  status=403
                                  )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]['description'], 'You can\'t change documents after rectification period')
