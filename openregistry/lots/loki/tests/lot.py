# -*- coding: utf-8 -*-
import os
import unittest

from openregistry.lots.core.tests.base import BaseWebTest, snitch
from openregistry.lots.core.tests.blanks.mixins import ResourceTestMixin
from openregistry.lots.loki.tests.base import (
    BaseLotWebTest
)
from openregistry.lots.loki.tests.json_data import test_loki_lot_data
from openregistry.lots.loki.tests.blanks.lot_blanks import (
    dateModified_resource,
    # LotResourceTest
    change_draft_lot,
    change_dissolved_lot,
    check_lot_assets,
    rectificationPeriod_workflow,
    check_decisions,
    change_pending_lot,
    change_composing_lot,
    change_verification_lot,
    change_pending_deleted_lot,
    change_deleted_lot,
    change_pending_dissolution_lot,
    change_active_salable_lot,
    change_active_auction_lot,
    change_active_contracting_lot,
    change_sold_lot,
    change_pending_sold_lot,
    auction_autocreation,
    check_change_to_verification,
    check_auction_status_lot_workflow,
    check_contract_status_workflow,
    adding_platformLegalDetails_doc,
    # LotTest
    simple_add_lot,
    simple_patch
)
from openregistry.lots.loki.models import Lot


class LotTest(BaseWebTest):
    initial_data = test_loki_lot_data
    relative_to = os.path.dirname(__file__)
    test_simple_add_lot = snitch(simple_add_lot)


class LotResourceTest(BaseLotWebTest, ResourceTestMixin):
    initial_status = 'pending'
    docservice = True
    lot_model = Lot
    maxDiff = None

    test_05_dateModified_resource = snitch(dateModified_resource)
    test_08_change_draft_lot = snitch(change_draft_lot)
    test_09_change_pending_lot = snitch(change_pending_lot)
    test_10_change_active_salable_lot = snitch(change_active_salable_lot)
    test_change_pending_deleted_lot = snitch(change_pending_deleted_lot)
    test_11_check_deleted_lot = snitch(change_deleted_lot)
    test_12_check_pending_dissolution_lot = snitch(change_pending_dissolution_lot)
    test_13_check_active_salable_lot = snitch(change_active_salable_lot)
    test_15_check_active_auction_lot = snitch(change_active_auction_lot)
    test_16_check_active_contracting_lot = snitch(change_active_contracting_lot)
    test_17_change_dissolved_lot = snitch(change_dissolved_lot)
    test_18_check_sold_lot = snitch(change_sold_lot)
    test_19_check_lot_assets = snitch(check_lot_assets)
    test_21_check_pending_sold_lot = snitch(change_pending_sold_lot)
    test_22_simple_patch = snitch(simple_patch)
    test_change_verification_lot = snitch(change_verification_lot)
    test_check_change_to_verification = snitch(check_change_to_verification)
    test_change_composing_lot = snitch(change_composing_lot)
    test_check_decisions = snitch(check_decisions)
    test_rectificationPeriod_workflow = snitch(rectificationPeriod_workflow)
    test_auction_autocreation = snitch(auction_autocreation)
    test_check_auction_status_lot_workflow = snitch(check_auction_status_lot_workflow)
    test_check_contract_status_workflow = snitch(check_contract_status_workflow)
    test_adding_platformLegalDetails_doc = snitch(adding_platformLegalDetails_doc)


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(LotResourceTest))
    tests.addTest(unittest.makeSuite(LotTest))
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
