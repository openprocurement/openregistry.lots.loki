# -*- coding: utf-8 -*-
import unittest

from openregistry.lots.basic.tests.base import LotContentWebTest
from openregistry.lots.core.tests.plugins.transferring.mixins import (
    LotOwnershipChangeTestCaseMixin
)


class LotOwnershipChangeResourceTest(LotContentWebTest,
                                     LotOwnershipChangeTestCaseMixin):

    def setUp(self):
        super(LotOwnershipChangeResourceTest, self).setUp()

        # needed to work with transfer resource
        self.resource_name = self.__class__.resource_name
        self.__class__.resource_name = ''

        self.not_used_transfer = self.create_transfer()

    def tearDown(self):
        super(LotOwnershipChangeResourceTest, self).tearDown()
        self.__class__.resource_name = self.resource_name

    def use_transfer(self, transfer, resource_id, origin_transfer):
        req_data = {"data": {"id": transfer['data']['id'],
                             'transfer': origin_transfer}}

        self.app.post_json(
            '{}/{}/ownership'.format(self.resource_name, resource_id), req_data
        )
        response = self.app.get('transfers/{}'.format(transfer['data']['id']))
        return response.json

    def create_transfer(self):
        response = self.app.post_json('transfers', {"data": {}})
        return response.json

    def get_resource(self, resource_id):
        response = self.app.get('{}/{}'.format(self.resource_name, resource_id))
        return response.json

    def set_resource_mode(self, resource_id, mode):
        current_auth = self.app.authorization

        self.app.authorization = ('Basic', ('administrator', ''))
        self.app.patch_json('{}/{}'.format(self.resource_name, resource_id),
                            {'data': {'mode': mode}})
        self.app.authorization = current_auth


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(LotOwnershipChangeResourceTest))
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
