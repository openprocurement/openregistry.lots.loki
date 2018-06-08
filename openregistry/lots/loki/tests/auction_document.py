# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy

from openregistry.lots.core.tests.base import snitch
from openregistry.lots.loki.tests.blanks.auction_document_blanks import (
    not_found_auction_document,
    put_auction_document,
    create_auction_document,
    patch_auction_document,
    model_validation,
    rectificationPeriod_document_workflow
)

from openregistry.lots.loki.tests.base import (
    LotContentWebTest
)
from openregistry.lots.loki.tests.json_data import test_loki_document_data
from openregistry.lots.loki.constants import AUCTION_DOCUMENT_TYPES


class LotAuctionDocumentWithDSResourceTest(LotContentWebTest):
    docservice = True
    document_types = AUCTION_DOCUMENT_TYPES
    initial_status = 'composing'

    test_not_found = snitch(not_found_auction_document)
    test_put_auction_document = snitch(put_auction_document)
    test_create_auction_document = snitch(create_auction_document)
    test_patch_auction_document = snitch(patch_auction_document)
    test_model_validation = snitch(model_validation)
    test_rectification_document_workflow = snitch(rectificationPeriod_document_workflow)

    # status, in which operations with lot documents (adding, updating) are forbidden
    forbidden_document_modification_actions_status = 'active.salable'

    def setUp(self):
        super(LotAuctionDocumentWithDSResourceTest, self).setUp()
        self.initial_document_data = deepcopy(test_loki_document_data)
        self.initial_document_data['documentOf'] = 'auction'
        self.initial_document_data['url'] = self.generate_docservice_url()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LotAuctionDocumentWithDSResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
