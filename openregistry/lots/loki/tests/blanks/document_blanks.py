# -*- coding: utf-8 -*-
from copy import deepcopy
from datetime import datetime, timedelta

from openregistry.lots.core.constants import TZ
from openregistry.lots.core.models import Period
from openregistry.lots.core.utils import get_now, calculate_business_date

from openregistry.lots.loki.models import Lot


def patch_resource_document(self):
    response = self.app.post_json('/{}/documents'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    #dateModified = response.json["data"]['dateModified']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual(u'укр.doc', response.json["data"]["title"])
    self.assertEqual(self.initial_document_data["documentType"], response.json["data"]['documentType'])

    response = self.app.patch_json('/{}/documents/{}'.format(self.resource_id, doc_id),
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

    response = self.app.patch_json('/{}/documents/{}'.format(self.resource_id, doc_id),
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
    response = self.app.patch_json('/{}/documents/{}'.format(self.resource_id, doc_id),
        headers=self.access_header, params={
            "data": {
                "description": "document description"
            }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual(self.initial_document_data["documentType"], response.json["data"]['documentType'])

    response = self.app.get('/{}/documents/{}'.format(self.resource_id, doc_id),
                            headers=self.access_header)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('document description', response.json["data"]["description"])
    #self.assertTrue(dateModified < response.json["data"]["dateModified"])

    self.set_status(self.forbidden_document_modification_actions_status)

    response = self.app.patch_json('/{}/documents/{}'.format(self.resource_id, doc_id),
        headers=self.access_header, params={
            "data": {
                "description": "document description"
            }}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"],
                     "Can't update document in current ({}) {} status".format(self.forbidden_document_modification_actions_status, self.resource_name[:-1]))


def model_validation(self):
    initial_document_data = deepcopy(self.initial_document_data)
    del initial_document_data['url']
    del initial_document_data['hash']
    initial_document_data['documentType'] = 'x_dgfAssetFamiliarization'
    response = self.app.post_json('/{}/documents'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': initial_document_data},
                                  status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'][0], u"This field is required.")

    initial_document_data['accessDetails'] = u'Some access details'
    response = self.app.post_json('/{}/documents'.format(self.resource_id),
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

    response = self.app.post_json('/{}/documents'.format(self.resource_id),
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

    response = self.app.post_json('/{}/documents'.format(lot['id']),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data},
                                  status=403
                                  )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'You can add only document with cancellationDetails after rectification period'
    )

    response = self.app.patch_json('/{}/documents/{}'.format(lot['id'], doc_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data},
                                  status=403
                                  )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]['description'], 'You can\'t change documents after rectification period')

    response = self.app.put_json('/{}/documents/{}'.format(lot['id'], doc_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data},
                                  status=403
                                  )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]['description'], 'You can\'t change documents after rectification period')


    test_document_data = {
        # 'url': self.generate_docservice_url(),
        'title': u'укр.doc',
        'hash': 'md5:' + '0' * 32,
        'format': 'application/msword',
        'documentType': 'cancellationDetails'
    }
    test_document_data['url'] = self.generate_docservice_url()

    response = self.app.post_json('/{}/documents'.format(lot['id']),
                                  headers=self.access_header,
                                  params={'data': test_document_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']

    response = self.app.patch_json('/{}/documents/{}'.format(lot['id'], doc_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data},
                                  status=403
                                  )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]['description'], 'You can\'t change documents after rectification period')

    response = self.app.put_json('/{}/documents/{}'.format(lot['id'], doc_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data},
                                  status=403
                                  )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]['description'], 'You can\'t change documents after rectification period')
