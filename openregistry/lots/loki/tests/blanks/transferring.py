# -*- coding: utf-8 -*-


def switch_mode(self):
    # set test mode and try to change ownership

    auth = ('Basic', (self.first_owner, ''))

    self.__class__.resource_name = self.resource_name
    resource = self.create_resource(auth=auth)
    resource_access_transfer = self.resource_transfer
    self.__class__.resource_name = ''

    # decision that was created from asset can't be updated (by patch)
    document = self.db.get(resource['id'])
    document['mode'] = 'test'
    self.db.save(document)

    self.app.authorization = ('Basic', (self.test_owner, ''))
    transfer = self.create_transfer()

    req_data = {"data": {"id": transfer['data']['id'],
                         'transfer': resource_access_transfer}}
    req_url = '{}/{}/ownership'.format(self.resource_name, resource['id'])

    response = self.app.post_json(req_url, req_data)

    self.assertEqual(response.status, '200 OK')
    self.assertIn('owner', response.json['data'])
    self.assertEqual(response.json['data']['owner'], self.test_owner)
