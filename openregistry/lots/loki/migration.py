# -*- coding: utf-8 -*-
import logging

from uuid import uuid4

from openregistry.lots.core.migration import (
    BaseMigrationsRunner,
    BaseMigrationStep,
)


LOGGER = logging.getLogger(__name__)


class LokiMigrationsRunner(BaseMigrationsRunner):

    SCHEMA_VERSION = 1
    SCHEMA_DOC = 'openregistry_lots_loki_schema'


class AddRelatedProcessesStep(BaseMigrationStep):

    def setUp(self):
        self.view = 'lot/all'

    def migrate_document(self, lot):
        if lot.get('relatedProcesses'):
            return

        self._migrate_assets_to_related_processes(lot)

        return lot

    def _migrate_assets_to_related_processes(self, lot):
        lot['relatedProcesses'] = []
        for asset_id in lot['assets']:
            related_process = {
                    'id': uuid4().hex,
                    'relatedProcessID': asset_id,
                    'type': 'asset'
                }
            if lot['status'] not in ['draft', 'composing', 'verification', 'invalid']:
                asset = self.resources.db.get(asset_id)
                related_process['identifier'] = asset['assetID']

            lot['relatedProcesses'].append(related_process)

        del lot['assets']


MIGRATION_STEPS = (
    AddRelatedProcessesStep,
)


def migrate(resources):
    runner = LokiMigrationsRunner(resources)
    runner.migrate(MIGRATION_STEPS)
