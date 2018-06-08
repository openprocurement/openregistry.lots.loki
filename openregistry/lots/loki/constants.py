# -*- coding: utf-8 -*-
from datetime import timedelta


AUCTION_STATUSES = ['scheduled', 'active', 'complete',  'unsuccessful', 'cancelled']

LOT_STATUSES = [
    "draft", "composing", "verification",  "pending", "pending.deleted", "deleted", "active.salable",
    "active.auction", "active.contracting", "pending.sold", "pending.dissolution", "sold", "dissolved", "invalid"]

ITEM_EDITING_STATUSES = ['draft', 'composing', 'pending']

STATUS_CHANGES = {
    "draft": {
        "editing_permissions": ["lot_owner", "Administrator"],
        "next_status": {
            "composing": ["lot_owner", "Administrator"],
        }
    },
    "composing": {
        "editing_permissions": ["lot_owner", "Administrator"],
        "next_status": {
            "verification": ["lot_owner", "Administrator"]
        }
    },
    "verification": {
        "editing_permissions": ["concierge"],
        "next_status": {
            "pending": ["concierge"],
            "invalid": ["concierge"],
        }
    },
    "pending": {
        "editing_permissions": ["lot_owner", "Administrator", "chronograph"],
        "next_status": {
            "pending.deleted": ["lot_owner", "Administrator"],
            "active.salable": ["chronograph", "Administrator"],
        }
    },
    "pending.deleted": {
        "editing_permissions": ["concierge", "Administrator"],
        "next_status": {
            "deleted": ["concierge", "Administrator"],
        }
    },
    "deleted": {
        "editing_permissions": [],
        "next_status": {}
    },
    "active.salable": {
        "editing_permissions": ["Administrator", "concierge"],
        "next_status": {
            "active.auction": ["Administrator", "concierge"]
        }
    },
    "active.auction": {
        "editing_permissions": ["Administrator"],
        "next_status": {
            "active.contracting": ["Administrator"],
            "pending.dissolution": ["Administrator"],
            "active.salable": ["Administrator"]
        }
    },
    "active.contracting": {
        "editing_permissions": ["Administrator"],
        "next_status": {
            "pending.sold": ["Administrator"],
            "pending.dissolution": ["Administrator"],
        }
    },
    "pending.sold": {
        "editing_permissions": ["Administrator", "concierge"],
        "next_status": {
            "sold": ["Administrator", "concierge"]
        }
    },
    "pending.dissolution": {
        "editing_permissions": ["Administrator", "concierge"],
        "next_status": {
            "dissolved": ["Administrator", "concierge"]
        }
    },
    "sold": {
        "editing_permissions": [],
        "next_status": {}
    },
    "dissolved": {
        "editing_permissions": [],
        "next_status": {}
    },
    "invalid": {
        "editing_permissions": [],
        "next_status": {}
    },
}
AUCTION_DOCUMENT_TYPES = [
    'notice',
    'technicalSpecifications',
    'evaluationCriteria',
    'illustration',
    'x_PublicAssetCertificate',
    'x_PlatformLegalDetails',
    'x_presentation',
    'bidders',
    'x_nda',
    'x_dgfAssetFamiliarization'
]

RECTIFICATION_PERIOD_DURATION = timedelta(days=2)
DEFAULT_DUTCH_STEPS = 99

DEFAULT_LOT_TYPE = 'loki'
DEFAULT_REGISTRATION_FEE = 17.0
