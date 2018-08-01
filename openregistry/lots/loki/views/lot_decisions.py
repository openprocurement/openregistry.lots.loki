# -*- coding: utf-8 -*-
from openregistry.lots.core.utils import (
    update_file_content_type,
    json_view,
    context_unpack,
    APIResource,
)
from openregistry.lots.core.utils import (
    save_lot, oplotsresource, apply_patch,
)
from openregistry.lots.core.validation import (
    validate_decision_post,
    validate_decision_after_rectificationPeriod,
    validate_decision_patch_data,
    validate_decision_update_in_not_allowed_status
)
from openregistry.lots.loki.validation import (
    validate_decision_by_decisionOf
)

post_validators = (
    validate_decision_post,
    validate_decision_after_rectificationPeriod,
    validate_decision_update_in_not_allowed_status
)
patch_validators = (
    validate_decision_patch_data,
    validate_decision_update_in_not_allowed_status,
    validate_decision_after_rectificationPeriod,
    validate_decision_by_decisionOf,
)


@oplotsresource(name='loki:Lot Decisions',
                collection_path='/lots/{lot_id}/decisions',
                path='/lots/{lot_id}/decisions/{decision_id}',
                _internal_type='loki',
                description="Lot related decisions")
class LotDecisionResource(APIResource):

    @json_view(permission='view_lot')
    def collection_get(self):
        """Lot Decision List"""
        collection_data = [i.serialize("view") for i in self.context.decisions]
        return {'data': collection_data}

    @json_view(content_type="application/json", permission='upload_lot_decisions', validators=post_validators)
    def collection_post(self):
        """Lot Decision Upload"""
        decision = self.request.validated['decision']
        self.context.decisions.append(decision)
        if save_lot(self.request):
            self.LOGGER.info(
                'Created lot decision {}'.format(decision.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'lot_decision_create'}, {'decision_id': decision.id})
            )
            self.request.response.status = 201
            decision_route = self.request.matched_route.name.replace("collection_", "")
            self.request.response.headers['Location'] = self.request.current_route_url(
                                                            _route_name=decision_route,
                                                            decision_id=decision.id,
                                                            _query={}
                                                            )
            return {'data': decision.serialize("view")}

    @json_view(permission='view_lot')
    def get(self):
        """Lot Decision Read"""
        decision = self.request.validated['decision']
        return {'data': decision.serialize("view")}

    @json_view(content_type="application/json", permission='upload_lot_decisions', validators=patch_validators)
    def patch(self):
        """Lot Decision Update"""
        if apply_patch(self.request, src=self.request.context.serialize()):
            update_file_content_type(self.request)
            self.LOGGER.info(
                'Updated lot decision {}'.format(self.request.context.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'lot_decision_patch'})
            )
            return {'data': self.request.context.serialize("view")}
