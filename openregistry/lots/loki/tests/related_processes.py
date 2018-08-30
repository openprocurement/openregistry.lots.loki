# -*- coding: utf-8 -*-
import unittest

from openregistry.lots.core.tests.base import snitch

from openregistry.lots.loki.tests.json_data import (
    test_related_process_data
)
from openregistry.lots.loki.tests.blanks.related_processes_blanks import (
    related_process_listing,
    create_related_process,
    patch_related_process,
    delete_related_process,
    patch_with_concierge,
    create_related_process_batch_mode
)
from openregistry.lots.loki.tests.base import (
    LotContentWebTest
)


class LotRelatedProcessResourceTest(LotContentWebTest):
    initial_status = 'draft'
    initial_related_process_data = test_related_process_data

    test_related_process_listing = snitch(related_process_listing)
    test_create_related_process = snitch(create_related_process)
    test_patch_related_process = snitch(patch_related_process)
    test_delete_related_process = snitch(delete_related_process)
    test_patch_with_concierge = snitch(patch_with_concierge)
    test_create_related_process_batch_mode = snitch(create_related_process_batch_mode)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LotRelatedProcessResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
