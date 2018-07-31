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
    patch_decisions_with_lot_by_concierge,
    rectificationPeriod_decision_workflow,
    create_or_patch_decision_in_not_allowed_status,
    create_decisions_with_lot
)


class LotDecisionResourceTest(LotContentWebTest):
    initial_decision_data = deepcopy(test_decision_data)

    test_create_decision = snitch(create_decision)
    test_patch_decision = snitch(patch_decision)
    test_patch_decisions_with_lot_by_broker = snitch(patch_decisions_with_lot_by_broker)
    test_patch_decisions_with_lot_by_concierge = snitch(patch_decisions_with_lot_by_concierge)
    test_rectificationPeriod_decision_workflow = snitch(rectificationPeriod_decision_workflow)
    test_create_or_patch_decision_in_not_allowed_status = snitch(create_or_patch_decision_in_not_allowed_status)
    test_create_decisions_with_lot = snitch(create_decisions_with_lot)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LotDecisionResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
