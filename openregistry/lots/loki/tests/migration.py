# -*- coding: utf-8 -*-
import unittest

from openregistry.lots.core.tests.base import MigrationResourcesDTO_mock
from openregistry.lots.loki.tests.base import BaseLotWebTest
from openregistry.lots.loki.tests.json_data import test_loki_lot_data
from openregistry.lots.loki.migration import (
    AddRelatedProcessesStep,
    LokiMigrationsRunner,
)


class MigrateTest(BaseLotWebTest):
    initial_data = test_loki_lot_data
    initial_status = 'draft'
    docservice = True

    def setUp(self):
        super(MigrateTest, self).setUp()
        migration_resources = MigrationResourcesDTO_mock(self.db)
        self.migration_runner = LokiMigrationsRunner(migration_resources)

    def test_migrate_draft_lot(self):
        # Create situation when we need migration for lot in status draft
        self.initial_status = 'draft'

        self.app.authorization = ('Basic', ('broker', ''))
        self.create_resource()
        lot = self.db.get(self.resource_id)

        if lot.get('relatedProcess', None) is not None:
            del lot['relatedProcess']

        assets = [
            '1' * 32
        ]
        lot['assets'] = assets
        self.db.save(lot)

        steps = (AddRelatedProcessesStep,)
        self.migration_runner.migrate(steps, schema_version_max=1)

        # Test if api works well
        # Test if migration change document
        response = self.app.get('/{}'.format(self.resource_id))
        self.assertNotIn('assets', response.json['data'])
        self.assertEqual(len(response.json['data']['relatedProcesses']), len(assets))

        asset_id = assets[0]
        related_process = response.json['data']['relatedProcesses'][0]

        self.assertEqual(related_process['relatedProcessID'], asset_id)
        self.assertEqual(related_process['type'], 'asset')
        self.assertIn('id', related_process)

        # Test patch goes well
        response = self.app.patch_json(
            '/{}'.format(self.resource_id),
            params={'data': {'status': 'composing'}},
            headers=self.access_header
        )
        self.assertEqual(response.json['data']['status'], 'composing')

        response = self.app.get('/{}'.format(self.resource_id))
        self.assertEqual(response.json['data']['status'], 'composing')

        # Get relatedProcesses
        response = self.app.get('/{}/related_processes'.format(self.resource_id))
        self.assertEqual(len(response.json['data']), 1)
        rp_id = response.json['data'][0]['id']

        response = self.app.get('/{}/related_processes/{}'.format(self.resource_id, rp_id))
        self.assertEqual(response.json['data']['id'], rp_id)
        self.assertEqual(response.json['data']['relatedProcessID'], assets[0])
        self.assertEqual(response.json['data']['type'], 'asset')

    def test_migrate_pending_lot(self):
        # Create situation when we need migration for lot in status pending
        self.initial_status = 'pending'

        self.app.authorization = ('Basic', ('broker', ''))
        self.create_resource()
        lot = self.db.get(self.resource_id)

        asset_1_data = {'assetID': '1-ASSET-ID'}

        asset_1 = self.db.save(asset_1_data)

        if lot.get('relatedProcess', None) is not None:
            del lot['relatedProcess']

        assets = [
            asset_1[0],
        ]
        lot['assets'] = assets
        self.db.save(lot)

        steps = (AddRelatedProcessesStep,)
        self.migration_runner.migrate(steps, schema_version_max=1)

        # Test if api works well
        # Test if migration change document
        response = self.app.get('/{}'.format(self.resource_id))
        self.assertNotIn('assets', response.json['data'])
        self.assertEqual(len(response.json['data']['relatedProcesses']), len(assets))

        asset_id = assets[0]
        related_process = response.json['data']['relatedProcesses'][0]

        self.assertEqual(related_process['relatedProcessID'], asset_id)
        self.assertEqual(related_process['type'], 'asset')
        self.assertEqual(related_process['identifier'], asset_1_data['assetID'])
        self.assertIn('id', related_process)

        # Test patch goes well
        self.app.authorization = ('Basic', ('broker', ''))
        test_document_data = dict(
            title=u'укр.doc',
            hash='md5:' + '0' * 32,
            format='application/msword',
            documentType='cancellationDetails'
        )
        test_document_data['url'] = self.generate_docservice_url()

        self.app.post_json(
            '/{}/documents'.format(self.resource_id),
            headers=self.access_header,
            params={'data': test_document_data})

        response = self.app.patch_json(
            '/{}'.format(self.resource_id),
            params={'data': {'status': 'pending.deleted'}},
            headers=self.access_header
        )
        self.assertEqual(response.json['data']['status'], 'pending.deleted')

        response = self.app.get('/{}'.format(self.resource_id))
        self.assertEqual(response.json['data']['status'], 'pending.deleted')

        # Get relatedProcesses
        response = self.app.get('/{}/related_processes'.format(self.resource_id))
        self.assertEqual(len(response.json['data']), 1)
        rp_id = response.json['data'][0]['id']

        response = self.app.get('/{}/related_processes/{}'.format(self.resource_id, rp_id))
        self.assertEqual(response.json['data']['id'], rp_id)
        self.assertEqual(response.json['data']['relatedProcessID'], assets[0])
        self.assertEqual(response.json['data']['type'], 'asset')
        self.assertEqual(response.json['data']['identifier'], asset_1_data['assetID'])


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(MigrateTest))
    return tests
