# -*- coding: utf-8 -*-
from openregistry.lots.core.adapters import (
    LotConfigurator,
    LotManagerAdapter
)
from openregistry.lots.core.validation import (
    validate_post_lot_role,

)
from openregistry.lots.core.utils import (
    get_now,
    calculate_business_date,
    apply_patch,
    save_lot
)
from openregistry.lots.loki.utils import (
    check_status,
    update_auctions
)
from .constants import (
    STATUS_CHANGES,
    RECTIFICATION_PERIOD_DURATION,
    ITEM_EDITING_STATUSES,
    DEFAULT_DUTCH_STEPS
)
from .validation import (
    validate_decision_post,
    validate_decision_patch,
    validate_deleted_status,
    validate_verification_status,
)


class LokiLotConfigurator(LotConfigurator):
    """ Loki Tender configuration adapter """

    name = "Loki Lot configurator"
    available_statuses = STATUS_CHANGES
    item_editing_allowed_statuses = ITEM_EDITING_STATUSES


class LokiLotManagerAdapter(LotManagerAdapter):
    name = 'Loki Lot Manager'
    create_validation = (
        validate_post_lot_role,
        validate_decision_post,
    )
    change_validation = (
        validate_decision_patch,
        validate_deleted_status,
        validate_verification_status,
    )

    def _set_rectificationPeriod(self, request):
        data = dict()
        data['startDate'] = get_now()
        data['endDate'] = calculate_business_date(
            data['startDate'],
            RECTIFICATION_PERIOD_DURATION,
            context=request.context)
        request.context.rectificationPeriod = type(request.context).rectificationPeriod.model_class(data)

    def _create_auctions(self, request):
        lot = request.validated['lot']
        lot.date = get_now()
        auction_types = ['sellout.english', 'sellout.english', 'sellout.insider']
        auction_class = lot.__class__.auctions.model_class
        for tenderAttempts, auction_type in enumerate(auction_types, 1):
            data = dict()
            data['tenderAttempts'] = tenderAttempts
            data['procurementMethodType'] = auction_type
            data['status'] = 'scheduled'
            data['auctionParameters'] = {}
            if auction_type == 'sellout.english':
                data['auctionParameters']['type'] = 'english'
            elif auction_type == 'sellout.insider':
                data['auctionParameters']['type'] = 'insider'
                data['auctionParameters']['dutchSteps'] = DEFAULT_DUTCH_STEPS
            data['__parent__'] = lot
            lot.auctions.append(auction_class(data))
        update_auctions(lot)

    def create_lot(self, request):
        self._validate(request, self.create_validation)
        self._create_auctions(request)

    def change_lot(self, request):
        self._validate(request, self.change_validation)
        if request.authenticated_role == 'chronograph':
            apply_patch(request, save=False, src=request.validated['lot_src'])
            check_status(request)
            save_lot(request)
        elif request.validated['data'].get('status') == 'pending' and not request.context.rectificationPeriod:
            self._set_rectificationPeriod(request)
