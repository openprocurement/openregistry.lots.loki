# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy

from openregistry.lots.core.tests.base import snitch

from openregistry.lots.loki.tests.base import (
    LotContentWebTest
)
from openregistry.lots.loki.tests.json_data import test_decision_data
from openregistry.lots.loki.tests.blanks.decision_blanks import (
    create_decision,
    patch_decision,
    patch_decisions_with_lot_by_broker,
    patch_decisions_with_lot_by_concierge
)


class LotDecisionResourceTest(LotContentWebTest):
    initial_decision_data = deepcopy(test_decision_data)

    test_create_decision = snitch(create_decision)
    test_patch_decision = snitch(patch_decision)
    test_patch_decisions_with_lot_by_broker = snitch(patch_decisions_with_lot_by_broker)
    test_patch_decisions_with_lot_by_concierge = snitch(patch_decisions_with_lot_by_concierge)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LotDecisionResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
