# -*- coding: utf-8 -*-
import unittest

from copy import deepcopy

from openregistry.lots.core.tests.base import (
    RelatedProcessesTestMixinBase,
)

from openregistry.lots.loki.tests.json_data import (
    test_related_process_data,
    test_loki_lot_data,
)
from openregistry.lots.loki.tests.base import (
    LotContentWebTest
)


class RelatedProcessesTestMixin(RelatedProcessesTestMixinBase):
    """These methods adapt test blank to the test case

    This adaptation is required because the mixin would test different types
    of resources, e.g. auctions, lots, assets.
    """

    def mixinSetUp(self):
        self.base_resource_initial_data = test_loki_lot_data
        self.rp_resource_collection_url = '/{}/related_processes'.format(self.resource_id)
        self.base_resource_url = '/'

        token = self.db[self.resource_id]['owner_token']
        self.access_header = {'X-Access-Token': str(token)}

        self.initial_related_process_data = test_related_process_data

    def test_create_2_related_processes_in_the_batch_mode(self):
        data = deepcopy(self.initial_data)
        related_process_1 = {
            'id': '1' * 32,
            'identifier': 'SOME-IDENTIFIER',
            'type': 'asset',
            'relatedProcessID': '2' * 32
        }
        data['relatedProcesses'] = (
           related_process_1,
           related_process_1,
        )
        response = self.app.post_json(
            '/',
            params={'data': data},
            status=422,
            headers=self.access_header
        )
        self.assertEqual(response.json['errors'][0]['description'][0], 'Please provide no more than 1 item.')

    def test_patch_related_process_in_not_allowed_status(self):
        self.mixinSetUp()

        # Create relatedProcess
        data = deepcopy(self.initial_related_process_data)
        response = self.app.post_json(
            self.rp_resource_collection_url,
            params={
                'data': data
            },
            headers=self.access_header
        )
        related_process_id = response.json['data']['id']

        new_data = {
            'relatedProcessID': '2' * 32
        }

        self.set_status('pending')
        response = self.app.patch_json(
            self.rp_resource_collection_url + '/' + related_process_id,
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

    def test_delete_relatedProcess_in_not_allowed_status(self):
        self.mixinSetUp()

        response = self.app.post_json(
            self.rp_resource_collection_url,
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
            self.rp_resource_collection_url + '/' + related_process_id,
            headers=self.access_header,
            status=403
        )
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(
            response.json['errors'][0]['description'],
            'Can\'t update relatedProcess in current ({}) lot status'.format('pending')
        )

        response = self.app.get(self.rp_resource_collection_url)
        self.assertEqual(len(response.json['data']), 1)

    def test_patch_relatedProcess_in_not_allowed_status(self):
        self.mixinSetUp()

        # Create relatedProcess
        response = self.app.post_json(
            self.rp_resource_collection_url,
            params={
                'data': self.initial_related_process_data
            },
            headers=self.access_header
        )
        self.assertEqual(response.status, '201 Created')
        related_process_id = response.json['data']['id']

        new_data = {
            'relatedProcessID': '2' * 32,
            'identifier': 'UA-SOME-VALUE'
        }

        self.app.authorization = ('Basic', ('concierge', ''))
        response = self.app.patch_json(
            self.rp_resource_collection_url + '/' + related_process_id,
            params={
                'data': new_data
            },
            status=403
        )
        self.assertEqual(response.status, '403 Forbidden')

        self.set_status('verification')

        # Patch relatedProcess
        response = self.app.patch_json(
            self.rp_resource_collection_url + '/' + related_process_id,
            params={'data': new_data}
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['id'], related_process_id)
        self.assertNotEqual(response.json['data']['relatedProcessID'], new_data['relatedProcessID'])
        self.assertEqual(response.json['data']['identifier'], new_data['identifier'])

        response = self.app.get(self.rp_resource_collection_url + '/' + related_process_id)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['id'], related_process_id)
        self.assertNotEqual(response.json['data']['relatedProcessID'], new_data['relatedProcessID'])
        self.assertEqual(response.json['data']['identifier'], new_data['identifier'])


class LotRelatedProcessResourceTest(LotContentWebTest, RelatedProcessesTestMixin):
    initial_status = 'draft'


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LotRelatedProcessResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
