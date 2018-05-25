# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy

from openregistry.lots.core.tests.base import snitch
from openregistry.lots.loki.tests.blanks.item_document_blanks import (
    not_found_item_document,
    put_item_document,
    create_item_document,
    patch_item_document,
    model_validation,
    rectificationPeriod_document_workflow
)

from openregistry.lots.loki.tests.base import (
    LotContentWebTest
)
from openregistry.lots.core.tests.blanks.json_data import test_loki_item_data
from openregistry.lots.core.constants import LOKI_DOCUMENT_TYPES
from openregistry.lots.loki.tests.json_data import test_loki_document_data
from openregistry.lots.loki.constants import LOT_STATUSES


class LotItemDocumentWithDSResourceTest(LotContentWebTest):
    docservice = True
    document_types = LOKI_DOCUMENT_TYPES
    initial_item_data = deepcopy(test_loki_item_data)

    test_not_found = snitch(not_found_item_document)
    test_put_item_document = snitch(put_item_document)
    test_create_item_document = snitch(create_item_document)
    test_patch_item_document = snitch(patch_item_document)
    test_model_validation = snitch(model_validation)
    test_rectification_document_workflow = snitch(rectificationPeriod_document_workflow)

    # status, in which operations with lot documents (adding, updating) are forbidden
    forbidden_item_document_statuses_modification = list(set(LOT_STATUSES) - {'draft', 'composing', 'pending'})

    def setUp(self):
        super(LotItemDocumentWithDSResourceTest, self).setUp()
        self.initial_document_data = deepcopy(test_loki_document_data)
        self.initial_document_data['documentOf'] = 'item'
        self.initial_document_data['documentType'] = 'notice'
        self.initial_document_data['url'] = self.generate_docservice_url()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LotItemDocumentWithDSResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
