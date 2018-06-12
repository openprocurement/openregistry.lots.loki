# -*- coding: utf-8 -*-
from copy import deepcopy
from datetime import timedelta

from openregistry.lots.core.utils import get_now
from openregistry.lots.core.tests.blanks.json_data import (
    test_document_data,
    test_item_data,
    test_organization
)

now = get_now()
test_loki_document_data = deepcopy(test_document_data)
test_loki_document_data['documentType'] = 'notice'
test_loki_document_data['documentOf'] = 'lot'

auction_common = {
    'auctionPeriod': {
        'startDate': (now + timedelta(days=5)).isoformat(),
        'endDate': (now + timedelta(days=10)).isoformat()
    },
    'value': {
        'amount': 3000.87,
        'currency': 'UAH',
        'valueAddedTaxIncluded': True
    },
    'minimalStep': {
        'amount': 300.87,
        'currency': 'UAH',
        'valueAddedTaxIncluded': True
    },
    'guarantee': {
        'amount': 700.87,
        'currency': 'UAH'
    },
    'registrationFee': {
        'amount': 700.87,
        'currency': 'UAH'
    }
}
auction_english_data = deepcopy(auction_common)

auction_second_english_data = {}
auction_second_english_data['tenderingDuration'] = 'P25DT12H'

# auction_insider_data = deepcopy(auction_common)


test_lot_auctions_data = {
    'english': auction_english_data,
    'second.english': auction_second_english_data,
    # 'insider': auction_insider_data
}


test_loki_lot_data = {
    "title": u"Тестовий лот",
    "description": u"Щось там тестове",
    "lotType": "loki",
    "assets": [],
    "decisions": [{
        'decisionDate': get_now().isoformat(),
        'decisionID': 'decisionLotID'
    }]
}

test_loki_item_data = deepcopy(test_item_data)
test_loki_item_data['registrationDetails'] = {
    'status': 'unknown'
}
test_loki_item_data.update(
    {
        "unit": {"code": "code"},
        "classification": {
            "scheme": "CAV",
            "id": "42111000-7",
            "description": "Description"
        },
        "address": {"countryName": "Ukraine"},
        "quantity": 5.0001,
        "additionalClassifications": [
            {
                "scheme": u"UA-EDR",
                "id": u"111111-4",
                "description": u"папір і картон гофровані, паперова й картонна тара"
            }
        ]
    }
)

test_lot_contract_data = {
    'contractID': 'contractID',
    'relatedProcessID': '1' * 32
}
