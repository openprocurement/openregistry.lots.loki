# -*- coding: utf-8 -*-
from openregistry.lots.loki.constants import (
    CONTRACT_TYPE
)

from openregistry.lots.loki.tests.base import create_single_lot, check_patch_status_200


def patch_contracts_by(self, role):
    response = self.app.get('/{}/contracts'.format(self.resource_id))
    contracts = response.json['data']
    contract = contracts[0]
    contract_id = contract['id']
    self.assertEqual(len(contracts), 1)
    self.assertEqual(contract['type'], CONTRACT_TYPE)
    self.assertEqual(contract['status'], 'scheduled')

    self.app.authorization = ('Basic', (role, ''))
    response = self.app.patch_json('/{}/contracts/{}'.format(self.resource_id, contract_id),
        headers=self.access_header, params={
            "data": self.initial_contract_data})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(contract_id, response.json["data"]["id"])
    self.assertEqual(response.json["data"]["type"], CONTRACT_TYPE)
    self.assertEqual(response.json["data"]["contractID"], self.initial_contract_data['contractID'])
    self.assertEqual(response.json["data"]["relatedProcessID"], self.initial_contract_data['relatedProcessID'])

    response = self.app.patch_json('/{}/contracts/{}'.format(self.resource_id, contract_id),
        headers=self.access_header, params={
            "data": {'type': 'WRONG', 'id': '1' * 32}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertIsNone(response.json)

    response = self.app.get('/{}/contracts'.format(self.resource_id))
    contracts = response.json['data']
    contract = contracts[0]
    self.assertEqual(len(contracts), 1)
    self.assertEqual(contract['type'], CONTRACT_TYPE)
    self.assertEqual(contract['id'], contract_id)

    # Patch status
    response = self.app.patch_json('/{}/contracts/{}'.format(self.resource_id, contract_id),
        headers=self.access_header, params={
            "data": {'status': 'active'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], 'active')

    response = self.app.get('/{}/contracts'.format(self.resource_id))
    contracts = response.json['data']
    contract = contracts[0]
    self.assertEqual(contract['status'], 'active')

    # Patch by broker
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.patch_json(
        '/{}/contracts/{}'.format(self.resource_id, contract_id),
        headers=self.access_header,
        params={
            "data": self.initial_contract_data
        },
        status=403
    )
    self.assertEqual(response.status, '403 Forbidden')

    # Invalid patch
    self.app.authorization = ('Basic', (role, ''))
    response = self.app.patch_json(
        '/{}/contracts/{}'.format(self.resource_id, contract_id),
        headers=self.access_header,
        params={
            "data": {'wrong_field': 'wrong_value'}
        },
        status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description'], 'Rogue field')


def patch_contracts_by_convoy(self):
    patch_contracts_by(self, 'convoy')


def patch_contracts_by_caravan(self):
    patch_contracts_by(self, 'caravan')


def patch_contracts_with_lot(self):
    self.app.authorization = ('Basic', ('broker', ''))

    response = create_single_lot(self, self.initial_data)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)

    # With two contracts
    data = {
        'contracts': [
                {'contractID': 'newContractID'},
                {'contractID': 'newContractID2'}
            ]
    }

    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        headers=access_header,
        params={'data': data},
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(len(response.json['data']['contracts']), 1)

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(len(response.json['data']['contracts']), 1)
    contracts = response.json['data']['contracts']
    contract = contracts[0]
    self.assertEqual(len(contracts), 1)
    self.assertEqual(contract['type'], CONTRACT_TYPE)
    self.assertNotIn('contractID', contract)
    self.assertNotIn('relatedProcessID', contract)

    # With one contract
    data = {
        'contracts':
            [
                {
                    'contractID': 'newContractID',
                    'relatedProcessID': 'newRelatedProcessID',
                    'type': 'new_type'
                }
            ]
    }

    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        headers=access_header,
        params={'data': data},
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(len(response.json['data']['contracts']), 1)

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(len(response.json['data']['contracts']), 1)
    contracts = response.json['data']['contracts']
    contract = contracts[0]
    self.assertEqual(len(contracts), 1)
    self.assertEqual(contract['type'], CONTRACT_TYPE)
    self.assertNotIn('contractID', contract)
    self.assertNotIn('relatedProcessID', contract)
