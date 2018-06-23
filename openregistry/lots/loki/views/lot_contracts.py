# -*- coding: utf-8 -*-
from openregistry.lots.core.utils import (
    json_view,
    context_unpack,
    APIResource,
)
from openregistry.lots.core.utils import (
    oplotsresource, apply_patch, save_lot
)
from openregistry.lots.loki.validation import (
    validate_contract_data,
    validate_patch_contract_data
)

post_validators = (
    validate_contract_data
)

patch_validators = (
    validate_patch_contract_data
)


@oplotsresource(name='loki:Lot Contracts',
                collection_path='/lots/{lot_id}/contracts',
                path='/lots/{lot_id}/contracts/{contract_id}',
                _internal_type='loki',
                description="Lot related contracts")
class LotContractResource(APIResource):

    @json_view(permission='view_lot')
    def collection_get(self):
        """Lot Contract List"""
        collection_data = [i.serialize("view") for i in self.context.contracts]
        return {'data': collection_data}

    @json_view(permission='view_lot')
    def get(self):
        """Lot Contract Read"""
        contract = self.request.validated['contract']
        return {'data': contract.serialize("view")}

    @json_view(content_type="application/json", permission='upload_lot_contracts', validators=post_validators)
    def collection_post(self):
        """Lot Contract Upload"""
        contract = self.request.validated['contract']
        contract.type = self.request.validated['lot'].lotType
        self.context.contracts.append(contract)
        if save_lot(self.request):
            self.LOGGER.info(
                'Created lot contract {}'.format(contract.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'lot_contract_create'}, {'contract_id': contract.id})
            )
            self.request.response.status = 201
            contract_route = self.request.matched_route.name.replace("collection_", "")
            self.request.response.headers['Location'] = self.request.current_route_url(
                                                            _route_name=contract_route,
                                                            contract_id=contract.id,
                                                            _query={}
                                                            )
            return {'data': contract.serialize("view")}

    @json_view(content_type="application/json", permission='upload_lot_contracts', validators=patch_validators)
    def patch(self):
        """Lot Contract Update"""
        apply_patch(self.request, save=False, src=self.request.context.serialize())
        if save_lot(self.request):
            self.LOGGER.info(
                'Updated lot contract {}'.format(self.request.context.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'lot_contract_patch'})
            )
            return {'data': self.request.context.serialize("view")}
