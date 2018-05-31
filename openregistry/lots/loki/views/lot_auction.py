# -*- coding: utf-8 -*-
from openregistry.lots.core.utils import (
    json_view,
    context_unpack,
    APIResource,
)
from openregistry.lots.core.utils import (
    oplotsresource, apply_patch, save_lot
)
from openregistry.lots.loki.utils import update_auctions, check_status
from openregistry.lots.loki.validation import (
    validate_auction_data,
    rectificationPeriod_auction_validation,
    validate_update_auction_in_not_allowed_status
)
patch_validators = (
    validate_auction_data,
    rectificationPeriod_auction_validation,
    validate_update_auction_in_not_allowed_status
)


@oplotsresource(name='loki:Lot Auctions',
                collection_path='/lots/{lot_id}/auctions',
                path='/lots/{lot_id}/auctions/{auction_id}',
                _internal_type='loki',
                description="Lot related auctions")
class LotAuctionResource(APIResource):

    @json_view(permission='view_lot')
    def collection_get(self):
        """Lot Auction List"""
        collection_data = [i.serialize("view") for i in self.context.auctions]
        return {'data': collection_data}

    @json_view(permission='view_lot')
    def get(self):
        """Lot Auction Read"""
        auction = self.request.validated['auction']
        return {'data': auction.serialize("view")}

    @json_view(content_type="application/json", permission='upload_lot_auctions', validators=(patch_validators))
    def patch(self):
        """Lot Auction Update"""
        apply_patch(self.request, save=False, src=self.request.context.serialize())
        update_auctions(self.request.validated['lot'])
        if self.request.authenticated_role == 'convoy':
            check_status(self.request)
        if save_lot(self.request):
            self.LOGGER.info(
                'Updated lot auction {}'.format(self.request.context.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'lot_auction_patch'})
            )
            return {'data': self.request.context.serialize("view")}
