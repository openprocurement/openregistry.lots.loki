# -*- coding: utf-8 -*-
import logging

from uuid import uuid4

from openregistry.lots.core.migration import (
    BaseMigrationsRunner,
    BaseMigrationStep,
)
from openregistry.lots.core.utils import (
    get_now,
)


LOGGER = logging.getLogger(__name__)


class LokiMigrationsRunner(BaseMigrationsRunner):

    SCHEMA_VERSION = 1
    SCHEMA_DOC = 'openregistry_lots_loki_schema'


class AddRelatedProcessesStep(BaseMigrationStep):

    def setUp(self):
        self.view = 'lot/all'

    def migrate_document(self, lot):
        lot_id = lot['_id']

        model = self._registry.lotTypes.get(lot['lotType'])

        if model._internal_type != 'loki':
            return

        if lot.get('relatedProcesses'):
            return

        if model:
            try:
                self._migrate_assets_to_related_processes(lot, self._registry)
                lot = model(lot)
                lot.__parent__ = self._root
                lot.validate()
                lot = lot.to_primitive()
            except:  # noqa E722
                LOGGER.error(
                    "Failed migration of lot {} to schema 1.".format(lot_id),
                    extra={'MESSAGE_ID': 'migrate_data_failed', 'LOT_ID': lot_id}
                )
            else:
                LOGGER.info(
                    "Migrated lot {} to schema 1.".format(lot_id),
                    extra={'MESSAGE_ID': 'migrate_data', 'LOT_ID': lot_id}
                )
                lot['dateModified'] = get_now().isoformat()
                return lot

    def _migrate_assets_to_related_processes(self, lot, registry):
        lot['relatedProcesses'] = []
        for asset_id in lot['assets']:
            related_process = {
                    'id': uuid4().hex,
                    'relatedProcessID': asset_id,
                    'type': 'asset'
                }
            if lot['status'] not in ['draft', 'composing', 'verification', 'invalid']:
                asset = registry.db.get(asset_id)
                related_process['identifier'] = asset['assetID']

            lot['relatedProcesses'].append(related_process)

        del lot['assets']


MIGRATION_STEPS = (
    AddRelatedProcessesStep,
)
