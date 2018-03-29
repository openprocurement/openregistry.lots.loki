# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy

from openprocurement.api.tests.base import snitch


from openregistry.lots.ssp.tests.base import (
    LotContentWebTest
)
from openprocurement.api.tests.blanks.json_data import test_ssp_publication_data
from openregistry.lots.ssp.tests.blanks.publication_blanks import (
    create_publication,
    patch_publication
)

class LotPublicationResourceTest(LotContentWebTest):
    initial_publication_data = deepcopy(test_ssp_publication_data)
    test_create_publication_resource = snitch(create_publication)
    test_patch_publication_resource = snitch(patch_publication)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LotPublicationResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
