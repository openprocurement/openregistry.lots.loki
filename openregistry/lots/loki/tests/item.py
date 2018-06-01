# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy

from openregistry.lots.core.tests.base import snitch

from openregistry.lots.loki.tests.base import (
    LotContentWebTest
)
from openregistry.lots.core.tests.blanks.json_data import test_loki_item_data
from openregistry.lots.loki.tests.blanks.item_blanks import (
    create_item_resource,
    patch_item,
    rectificationPeriod_item_workflow,
    update_items_in_forbidden,
    list_item_resource,
    patch_items_with_lot
)
from openregistry.lots.loki.constants import LOT_STATUSES


class LotItemResourceTest(LotContentWebTest):
    initial_item_data = deepcopy(test_loki_item_data)
    test_create_item_resource = snitch(create_item_resource)
    test_patch_item_resource = snitch(patch_item)
    test_rectificationPeriod_item_workflow = snitch(rectificationPeriod_item_workflow)
    test_list_item_resource = snitch(list_item_resource)
    test_update_items_in_forbidden = snitch(update_items_in_forbidden)
    test_patch_items_with_lot = snitch(patch_items_with_lot)

    forbidden_item_statuses_modification = list(set(LOT_STATUSES) - {'draft', 'composing', 'pending'})


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LotItemResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
