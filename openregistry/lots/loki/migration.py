# -*- coding: utf-8 -*-
import logging

from uuid import uuid4

from openregistry.lots.core.migration import (
    BaseMigrationsRunner,
    BaseMigrationStep,
)
from openregistry.lots.core.traversal import Root
from openregistry.lots.core.utils import (
    get_now, get_plugins
)

LOGGER = logging.getLogger(__name__)
SCHEMA_VERSION = 1
SCHEMA_DOC = 'openregistry_lots_loki_schema'


def get_db_schema_version(db):
    schema_doc = db.get(SCHEMA_DOC, {"_id": SCHEMA_DOC})
    return schema_doc.get("version", SCHEMA_VERSION - 1)


def set_db_schema_version(db, version):
    schema_doc = db.get(SCHEMA_DOC, {"_id": SCHEMA_DOC})
    schema_doc["version"] = version
    db.save(schema_doc)


def migrate_data(registry, destination=None):
    plugins_config = registry.app_meta.plugins
    existing_plugins = get_plugins(plugins_config)
    if registry.app_meta.plugins and not any(existing_plugins):
        return
    cur_version = get_db_schema_version(registry.db)
    if cur_version == SCHEMA_VERSION:
        return cur_version
    for step in xrange(cur_version, destination or SCHEMA_VERSION):
        LOGGER.info(
            "Migrate openregistry loki lot schema from {} to {}".format(step, step + 1),
            extra={'MESSAGE_ID': 'migrate_data'}
        )
        migration_func = globals().get('from{}to{}'.format(step, step + 1))
        if migration_func:
            migration_func(registry)
        set_db_schema_version(registry.db, step + 1)


def from0to1(registry):
    class Request(object):
        def __init__(self, registry):
            self.registry = registry

    results = registry.db.iterview('lot/all', 2 ** 10, include_docs=True)

    request = Request(registry)
    root = Root(request)

    docs = []
    for i in results:
        lot = i.doc
        lot_id = lot['_id']

        model = registry.lotTypes.get(lot['lotType'])

        if model._internal_type != 'loki':
            return

        if lot.get('relatedProcesses'):
            return

        if model:
            try:
                migrate_assets_to_related_processes(lot, registry)
                lot = model(lot)
                lot.__parent__ = root
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
                docs.append(lot)
        if len(docs) >= 2 ** 7:  # pragma: no cover
            registry.db.update(docs)
            docs = []
    if docs:
        registry.db.update(docs)


def migrate_assets_to_related_processes(lot, registry):
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
                migrate_assets_to_related_processes(lot, self._registry)
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
