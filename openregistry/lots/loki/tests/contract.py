# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy

from openregistry.lots.core.tests.base import snitch

from openregistry.lots.loki.tests.base import (
    LotContentWebTest
)
from openregistry.lots.loki.tests.json_data import test_lot_contract_data
from openregistry.lots.loki.tests.blanks.contract_blanks import (
    patch_contracts_by_convoy,
    patch_contracts_by_caravan,
    patch_contracts_with_lot
)


class LotContractResourceTest(LotContentWebTest):
    initial_contract_data = deepcopy(test_lot_contract_data)

    test_patch_contracts_by_convoy = snitch(patch_contracts_by_convoy)
    test_patch_contracts_by_caravan = snitch(patch_contracts_by_caravan)
    test_patch_contracts_with_lot = snitch(patch_contracts_with_lot)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LotContractResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
