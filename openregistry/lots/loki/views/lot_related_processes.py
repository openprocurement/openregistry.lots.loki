# -*- coding: utf-8 -*-
from pyramid.httpexceptions import HTTPNoContent
from openregistry.lots.core.utils import (
    json_view,
    context_unpack,
    APIResource,
)
from openregistry.lots.core.utils import (
    save_lot, oplotsresource, apply_patch,
)
from openregistry.lots.core.interfaces import ILotManager
from openregistry.lots.loki.validation import (
    validate_related_process_data,
    validate_patch_related_process_data,
    validate_related_process_operation_in_not_allowed_lot_status
)

post_validators = (
    validate_related_process_data,
    validate_related_process_operation_in_not_allowed_lot_status
)
patch_validators = (
    validate_patch_related_process_data,
    validate_related_process_operation_in_not_allowed_lot_status
)
delete_validators = (
    validate_related_process_operation_in_not_allowed_lot_status
)


@oplotsresource(name='loki:Lot Related Processes',
                collection_path='/lots/{lot_id}/related-processes',
                path='/lots/{lot_id}/related-processes/{relatedProcess_id}',
                _internal_type='loki',
                description="Lot related process")
class LotRelatedProcessResource(APIResource):

    @json_view(permission='view_lot')
    def collection_get(self):
        """Lot Related Process List"""
        collection_data = [i.serialize("view") for i in self.context.relatedProcesses]
        return {'data': collection_data}

    @json_view(content_type="application/json", permission='upload_lot_related_processes', validators=post_validators)
    def collection_post(self):
        """Lot Related Process Upload"""
        related_process = self.request.validated['relatedProcess']
        self.request.registry.getAdapter(self.request.validated['lot'], ILotManager).related_processes_manager.create(self.request)

        if save_lot(self.request):
            self.LOGGER.info(
                'Created lot related process {}'.format(related_process.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'lot_related_processes_create'}, {'related_process': related_process.id})
            )
            self.request.response.status = 201
            related_process_route = self.request.matched_route.name.replace("collection_", "")
            self.request.response.headers['Location'] = self.request.current_route_url(
                                                            _route_name=related_process_route,
                                                            relatedProcess_id=related_process.id,
                                                            _query={}
                                                            )
            return {'data': related_process.serialize("view")}

    @json_view(permission='view_lot')
    def get(self):
        """Lot Related Process Read"""
        related_process = self.request.validated['relatedProcess']
        return {'data': related_process.serialize("view")}

    @json_view(content_type="application/json", permission='upload_lot_related_processes', validators=patch_validators)
    def patch(self):
        """Lot Related Process Update"""
        self.request.registry.getAdapter(self.request.validated['lot'], ILotManager).related_processes_manager.update(self.request)
        if apply_patch(self.request, src=self.request.context.serialize()):
            self.LOGGER.info(
                'Updated lot relatedProcess {}'.format(self.request.context.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'lot_related_process_patch'})
            )
            return {'data': self.request.context.serialize("view")}

    @json_view(permission='upload_lot_related_processes', validators=delete_validators)
    def delete(self):
        """Lot Related Process Delete"""
        self.request.registry.getAdapter(self.request.validated['lot'], ILotManager).related_processes_manager.delete(self.request)
        if save_lot(self.request):
            self.LOGGER.info(
                'Delete relatedProcess {}'.format(self.request.context.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'lot_related_process_patch'})
            )
            return {'data': self.request.context.serialize("view")}
