# -*- coding: utf-8 -*-

from schematics.transforms import blacklist, whitelist
from openregistry.lots.core.models import (
    plain_role,
    listing_role
)
from openregistry.lots.core.models import (
    schematics_default_role,
    schematics_embedded_role
)


item_create_role = blacklist('id')
item_edit_role = blacklist('id')
item_view_role = (schematics_default_role + blacklist())


item_roles = {
    'create': item_create_role,
    'edit': item_edit_role,
    'view': item_view_role,
}

auction_create_role = blacklist('id', 'status', 'auctionID', 'procurementMethodType')
auction_common_edit_role = blacklist('id', 'auctionID', 'procurementMethodType', 'tenderAttempts', 'status')
auction_view_role = (schematics_default_role + blacklist())
edit_first_english = (auction_common_edit_role + blacklist('tenderingDuration'))
edit_second_english = (
    auction_common_edit_role +
    blacklist('value', 'minimalStep', 'guarantee', 'registrationFee', 'auctionPeriod'))
edit_insider = (
    auction_common_edit_role +
    blacklist('tenderingDuration', 'value', 'minimalStep', 'guarantee', 'registrationFee', 'auctionPeriod')
)

auction_roles = {
    'create': auction_create_role,
    'edit': auction_common_edit_role,
    'view': auction_view_role,
    'edit_1.sellout.english': edit_first_english,
    'edit_2.sellout.english': edit_second_english,
    'edit_3.sellout.insider': edit_insider
}

english_auctionParameters_edit_role = blacklist('type', 'dutchSteps')
insider_auctionParameters_edit_role = blacklist('type')
auctionParameters_roles = {
    'create': blacklist('type', 'dutchSteps'),
    'edit_1.sellout.english': english_auctionParameters_edit_role,
    'edit_2.sellout.english': english_auctionParameters_edit_role,
    'edit_3.sellout.insider': insider_auctionParameters_edit_role
}

lot_create_role = (whitelist('status', 'assets', 'decisions', 'lotType', 'lotIdentifier', 'mode'))
lot_edit_role = (blacklist('owner_token', 'owner', '_attachments',
                       'revisions', 'date', 'dateModified', 'documents', 'decisions',
                       'lotID', 'mode', 'doc_id', 'items', 'rectificationPeriod') + schematics_embedded_role)
view_role = (blacklist('owner_token',
                       '_attachments', 'revisions') + schematics_embedded_role)

Administrator_role = whitelist('status', 'mode')
concierge_role = (blacklist(
    'owner_token', 'owner', '_attachments', 'revisions', 'date', 'dateModified',
    'lotID', 'mode', 'doc_id') + schematics_embedded_role)

lot_roles = {
    'create': lot_create_role,
    'plain': plain_role,
    'edit': lot_edit_role,
    'view': view_role,
    'listing': listing_role,
    'default': schematics_default_role,
    'Administrator': Administrator_role,
    # Draft role
    'draft': view_role,
    'edit_draft': whitelist('status'),
    # Composing role
    'composing': view_role,
    'edit_composing': whitelist('status'),
    'verification': view_role,
    'edit_verification': whitelist(),
    # Pending role
    'pending': view_role,
    'edit_pending': lot_edit_role,
    'edit_pendingAfterRectificationPeriod': whitelist('status'),
    # Pending.deleted role
    'pending.deleted': view_role,
    'edit_pending.deleted': whitelist(),
    # Deleted role
    'deleted': view_role,
    'edit_deleted': whitelist(),
    # Active.salable role
    'active.salable': view_role,
    'edit_active.salable': whitelist(),
    # pending.dissolution role
    'pending.dissolution': view_role,
    'edit_pending.dissolution': whitelist(),
    # Dissolved role
    'dissolved': view_role,
    'edit_dissolved': whitelist(),
    # Active.awaiting role
    'active.awaiting': view_role,
    'edit_active.awaiting': whitelist(),
    # Active.auction role
    'active.auction': view_role,
    'edit_active.auction': whitelist(),
    # Active.contracting role
    'active.contracting': view_role,
    'edit_active.contracting': whitelist(),
    # pending.sold role
    'pending.sold': view_role,
    'edit.pending.sold': whitelist(),
    # Sold role
    'sold': view_role,
    'edit.sold': whitelist(),
    'invalid': view_role,
    'edit.invalid': whitelist(),
    'concierge': whitelist('status', 'decisions', 'title', 'lotCustodian', 'description', 'lotHolder', 'items'),
    'convoy': whitelist('status', 'auctions')
}
