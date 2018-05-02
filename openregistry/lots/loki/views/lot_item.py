# -*- coding: utf-8 -*-
from openregistry.lots.core.utils import (
    get_file,
    update_file_content_type,
    json_view,
    context_unpack,
    APIResource,
)
from openregistry.lots.core.utils import (
    save_lot, oplotsresource, apply_patch,
)
from openregistry.lots.core.validation import (
    validate_update_item_in_not_allowed_status
)
from openregistry.lots.loki.validation import (
    validate_item_data,
    rectificationPeriod_item_validation,
)

post_validators = (
    validate_item_data,
    rectificationPeriod_item_validation,
    validate_update_item_in_not_allowed_status
)
patch_validators = (
    validate_item_data,
    rectificationPeriod_item_validation,
    validate_update_item_in_not_allowed_status
)


@oplotsresource(name='loki:Lot Items',
                collection_path='/lots/{lot_id}/items',
                path='/lots/{lot_id}/items/{item_id}',
                lotType='loki',
                description="Lot related items")
class LotItemResource(APIResource):

    @json_view(permission='view_lot')
    def collection_get(self):
        """Lot Item List"""
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in self.context.items]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in self.context.items
            ]).values(), key=lambda i: i['dateModified'])
        return {'data': collection_data}

    @json_view(content_type="application/json", permission='upload_lot_items', validators=(post_validators))
    def collection_post(self):
        """Lot Item Upload"""
        item = self.request.validated['item']
        self.context.items.append(item)
        if save_lot(self.request):
            self.LOGGER.info('Created lot item {}'.format(item.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'lot_item_create'}, {'item_id': item.id}))
            self.request.response.status = 201
            item_route = self.request.matched_route.name.replace("collection_", "")
            self.request.response.headers['Location'] = self.request.current_route_url(_route_name=item_route, item_id=item.id, _query={})
            return {'data': item.serialize("view")}

    @json_view(permission='view_lot')
    def get(self):
        """Lot Item Read"""
        item = self.request.validated['item']
        return {'data': item.serialize("view")}

    @json_view(content_type="application/json", permission='upload_lot_items', validators=(patch_validators))
    def patch(self):
        """Lot Item Update"""
        if apply_patch(self.request, src=self.request.context.serialize()):
            update_file_content_type(self.request)
            self.LOGGER.info('Updated lot item {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'lot_item_patch'}))
            return {'data': self.request.context.serialize("view")}
