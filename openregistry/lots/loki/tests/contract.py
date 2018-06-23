# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy

from openregistry.lots.core.tests.base import snitch

from openregistry.lots.loki.tests.base import (
    LotContentWebTest
)
from openregistry.lots.loki.tests.json_data import test_lot_contract_data
from openregistry.lots.loki.tests.blanks.contract_blanks import (
    patch_contract_by_caravan,
    patch_contract_by_convoy,
    patch_contracts_with_lot,
    create_contract_by_caravan,
    create_contract_by_convoy
)


class LotAuctionResourceTest(LotContentWebTest):
    initial_contract_data = deepcopy(test_lot_contract_data)

    test_patch_contracts_with_lot = snitch(patch_contracts_with_lot)
    test_patch_contract_by_caravan = snitch(patch_contract_by_caravan)
    test_patch_contract_by_convoy = snitch(patch_contract_by_convoy)
    test_create_contract_by_caravan = snitch(create_contract_by_caravan)
    test_create_contract_by_convoy = snitch(create_contract_by_convoy)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LotAuctionResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
