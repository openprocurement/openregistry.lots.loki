# -*- coding: utf-8 -*-
from copy import deepcopy


def related_process_listing(self):
    response = self.app.get('/{}/related_processes'.format(self.resource_id))
    self.assertEqual(len(response.json['data']), 0)

    response = self.app.post_json(
        '/{}/related_processes'.format(self.resource_id),
        params={
            'data': self.initial_related_process_data
        },
        headers=self.access_header
    )
    self.assertEqual(response.status, '201 Created')
    self.assertIn('id', response.json['data'])
    self.assertEqual(response.json['data']['relatedProcessID'], self.initial_related_process_data['relatedProcessID'])
    self.assertEqual(response.json['data']['type'], self.initial_related_process_data['type'])

    response = self.app.get('/{}/related_processes'.format(self.resource_id))
    self.assertEqual(len(response.json['data']), 1)


def create_related_process(self):
    response = self.app.get('/{}/related_processes'.format(self.resource_id))
    self.assertEqual(len(response.json['data']), 0)

    data = deepcopy(self.initial_related_process_data)
    data['identifier'] = 'UA-SOME-VALUE'
    data['id'] = '1' * 32

    # Create relatedProcess
    response = self.app.post_json(
        '/{}/related_processes'.format(self.resource_id),
        params={
            'data': data
        },
        headers=self.access_header
    )
    self.assertEqual(response.status, '201 Created')
    self.assertIn('id', response.json['data'])
    self.assertNotEqual(response.json['data']['id'], data['id'])
    self.assertNotIn('identifier', response.json['data'])
    self.assertEqual(response.json['data']['relatedProcessID'], self.initial_related_process_data['relatedProcessID'])
    self.assertEqual(response.json['data']['type'], self.initial_related_process_data['type'])

    response = self.app.get('/{}/related_processes'.format(self.resource_id))
    self.assertEqual(len(response.json['data']), 1)

    # Create relatedProcess when Lot already has one
    response = self.app.post_json(
        '/{}/related_processes'.format(self.resource_id),
        params={
            'data': data
        },
        status=422,
        headers=self.access_header
    )
    self.assertEqual(response.json['errors'][0]['description'][0], 'Please provide no more than 1 item.')

    response = self.app.get('/{}/related_processes'.format(self.resource_id))
    self.assertEqual(len(response.json['data']), 1)

    # Create relatedProcess in not allowed status
    self.create_resource()
    self.set_status('pending')
    response = self.app.post_json(
        '/{}/related_processes'.format(self.resource_id),
        params={
            'data': self.initial_related_process_data
        },
        headers=self.access_header,
        status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'Can\'t update relatedProcess in current ({}) lot status'.format('pending')
    )

    response = self.app.get('/{}/related_processes'.format(self.resource_id))
    self.assertEqual(len(response.json['data']), 0)


def patch_related_process(self):
    response = self.app.get('/{}/related_processes'.format(self.resource_id))
    self.assertEqual(len(response.json['data']), 0)

    data = deepcopy(self.initial_related_process_data)

    # Create relatedProcess
    response = self.app.post_json(
        '/{}/related_processes'.format(self.resource_id),
        params={
            'data': data
        },
        headers=self.access_header
    )
    related_process_id = response.json['data']['id']
    self.assertEqual(response.status, '201 Created')
    self.assertIn('id', response.json['data'])
    self.assertEqual(response.json['data']['relatedProcessID'], self.initial_related_process_data['relatedProcessID'])
    self.assertEqual(response.json['data']['type'], self.initial_related_process_data['type'])

    new_data = {
        'relatedProcessID': '2' * 32
    }

    # Patch relatedProcess
    response = self.app.patch_json(
        '/{}/related_processes/{}'.format(self.resource_id, related_process_id),
        params={
            'data': new_data
        },
        headers=self.access_header
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['id'], related_process_id)
    self.assertEqual(response.json['data']['relatedProcessID'], new_data['relatedProcessID'])
    self.assertEqual(response.json['data']['type'], self.initial_related_process_data['type'])

    response = self.app.get(
        '/{}/related_processes/{}'.format(self.resource_id, related_process_id),
        params={
            'data': new_data
        },
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['id'], related_process_id)
    self.assertEqual(response.json['data']['relatedProcessID'], new_data['relatedProcessID'])
    self.assertEqual(response.json['data']['type'], self.initial_related_process_data['type'])

    # Patch relatedProcess in not allowed status
    self.set_status('pending')
    response = self.app.patch_json(
        '/{}/related_processes/{}'.format(self.resource_id, related_process_id),
        params={
            'data': new_data
        },
        status=403,
        headers=self.access_header
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'Can\'t update relatedProcess in current ({}) lot status'.format('pending')
    )


def delete_related_process(self):
    response = self.app.get('/{}/related_processes'.format(self.resource_id))
    self.assertEqual(len(response.json['data']), 0)

    # Create relatedProcess
    response = self.app.post_json(
        '/{}/related_processes'.format(self.resource_id),
        params={
            'data': self.initial_related_process_data
        },
        headers=self.access_header
    )
    related_process_id = response.json['data']['id']
    self.assertEqual(response.status, '201 Created')
    self.assertIn('id', response.json['data'])
    self.assertEqual(response.json['data']['relatedProcessID'], self.initial_related_process_data['relatedProcessID'])
    self.assertEqual(response.json['data']['type'], self.initial_related_process_data['type'])

    response = self.app.get('/{}/related_processes'.format(self.resource_id))
    self.assertEqual(len(response.json['data']), 1)

    # Delete relatedProcess
    response = self.app.delete(
        '/{}/related_processes/{}'.format(self.resource_id, related_process_id),
        headers=self.access_header
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['id'], related_process_id)

    response = self.app.get('/{}/related_processes'.format(self.resource_id))
    self.assertEqual(len(response.json['data']), 0)

    # Delete relatedProcess in not allowed status
    response = self.app.post_json(
        '/{}/related_processes'.format(self.resource_id),
        params={
            'data': self.initial_related_process_data
        },
        headers=self.access_header
    )
    related_process_id = response.json['data']['id']
    self.assertEqual(response.status, '201 Created')
    self.assertIn('id', response.json['data'])
    self.assertEqual(response.json['data']['relatedProcessID'], self.initial_related_process_data['relatedProcessID'])
    self.assertEqual(response.json['data']['type'], self.initial_related_process_data['type'])

    self.set_status('pending')
    response = self.app.delete(
        '/{}/related_processes/{}'.format(self.resource_id, related_process_id),
        headers=self.access_header,
        status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'Can\'t update relatedProcess in current ({}) lot status'.format('pending')
    )

    response = self.app.get('/{}/related_processes'.format(self.resource_id))
    self.assertEqual(len(response.json['data']), 1)


def patch_with_concierge(self):
    response = self.app.get('/{}/related_processes'.format(self.resource_id))
    self.assertEqual(len(response.json['data']), 0)

    # Create relatedProcess
    response = self.app.post_json(
        '/{}/related_processes'.format(self.resource_id),
        params={
            'data': self.initial_related_process_data
        },
        headers=self.access_header
    )
    self.assertEqual(response.status, '201 Created')
    related_process_id = response.json['data']['id']
    self.assertIn('id', response.json['data'])
    self.assertEqual(response.json['data']['relatedProcessID'], self.initial_related_process_data['relatedProcessID'])
    self.assertEqual(response.json['data']['type'], self.initial_related_process_data['type'])

    new_data = {
        'relatedProcessID': '2' * 32,
        'identifier': 'UA-SOME-VALUE'
    }

    # Patch relatedProcess in not allowed status
    self.app.authorization = ('Basic', ('concierge', ''))
    response = self.app.patch_json(
        '/{}/related_processes/{}'.format(self.resource_id, related_process_id),
        params={
            'data': new_data
        },
        status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'Can\'t update relatedProcess in current ({}) lot status by concierge'.format(self.initial_status)
    )

    self.set_status('verification')

    # Patch relatedProcess
    response = self.app.patch_json(
        '/{}/related_processes/{}'.format(self.resource_id, related_process_id),
        params={
            'data': new_data
        }
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['id'], related_process_id)
    self.assertNotEqual(response.json['data']['relatedProcessID'], new_data['relatedProcessID'])
    self.assertEqual(response.json['data']['identifier'], new_data['identifier'])

    response = self.app.get(
        '/{}/related_processes/{}'.format(self.resource_id, related_process_id),
        params={
            'data': new_data
        },
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['id'], related_process_id)
    self.assertNotEqual(response.json['data']['relatedProcessID'], new_data['relatedProcessID'])
    self.assertEqual(response.json['data']['identifier'], new_data['identifier'])
