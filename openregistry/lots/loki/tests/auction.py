# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy

from openregistry.lots.core.tests.base import snitch

from openregistry.lots.loki.tests.base import (
    LotContentWebTest
)
from openregistry.lots.loki.tests.json_data import test_lot_auctions_data
from openregistry.lots.loki.tests.blanks.auction_blanks import (
    patch_english_auction,
    patch_second_english_auction,
    patch_insider_auction,
    rectificationPeriod_auction_workflow,
    procurementMethodDetails_check_with_sandbox,
    procurementMethodDetails_check_without_sandbox,
    submissionMethodDetails_check
)

class LotAuctionResourceTest(LotContentWebTest):
    initial_auctions_data = deepcopy(test_lot_auctions_data)

    test_patch_english_auction = snitch(patch_english_auction)
    test_patch_second_english_auction = snitch(patch_second_english_auction)
    test_patch_insider_auction = snitch(patch_insider_auction)
    test_rectificationPeriod_auction_workflow = snitch(rectificationPeriod_auction_workflow)
    test_procurementMethodDetails_check_with_sandbox = snitch(procurementMethodDetails_check_with_sandbox)
    test_procurementMethodDetails_check_without_sandbox = snitch(procurementMethodDetails_check_without_sandbox)
    submissionMethodDetails_check_without_sandbox = snitch(submissionMethodDetails_check)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LotAuctionResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
