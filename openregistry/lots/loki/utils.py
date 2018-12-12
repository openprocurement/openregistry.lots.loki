# -*- coding: utf-8 -*-
from openregistry.lots.core.utils import get_now, context_unpack, LOGGER
from decimal import Decimal, ROUND_HALF_UP


def check_status(request):
    lot = request.validated['lot']
    now = get_now()
    check_lot_status(request, lot, now)


def check_lot_status(request, lot, now=None):
    if not now:
        now = get_now()

    if lot.status == 'pending' and lot.rectificationPeriod.endDate <= now:
        LOGGER.info('Switched lot %s to %s', lot.id, 'active.salable',
                    extra=context_unpack(request, {'MESSAGE_ID': 'switched_lot_active.salable'}))
        lot.status = 'active.salable'


def process_convoy_auction_report_result(request):
    lot = request.validated['lot']

    is_lot_need_to_be_dissolved = bool(
        request.validated['auction'].status == 'cancelled' or
        all([auction.status == 'unsuccessful' for auction in lot.auctions])
    )

    if lot.status == 'active.auction' and is_lot_need_to_be_dissolved:
        LOGGER.info('Switched lot %s to %s', lot.id, 'pending.dissolution',
                    extra=context_unpack(request, {'MESSAGE_ID': 'switched_lot_pending.dissolution'}))

        lot.status = 'pending.dissolution'
        lot.contracts[0].status = 'cancelled'

        for auction in lot.auctions[request.validated['auction'].tenderAttempts:]:
            auction.status = 'cancelled'

    elif lot.status == 'active.auction' and request.validated['auction'].status == 'unsuccessful':
        LOGGER.info('Switched lot %s to %s', lot.id, 'active.salable',
                    extra=context_unpack(request, {'MESSAGE_ID': 'switched_lot_active.salable'}))
        lot.status = 'active.salable'
    elif lot.status == 'active.auction' and request.validated['auction'].status == 'complete':
        LOGGER.info('Switched lot %s to %s', lot.id, 'active.contracting',
                    extra=context_unpack(request, {'MESSAGE_ID': 'switched_lot_active.contracting'}))
        lot.status = 'active.contracting'
        for auction in lot.auctions[request.validated['auction'].tenderAttempts:]:
            auction.status = 'cancelled'


def process_concierge_auction_status_change(request):
    lot = request.validated['lot']

    if lot.status == 'active.salable' and request.validated['auction'].status == 'active':
        LOGGER.info('Switched lot %s to %s', lot.id, 'active.auction',
                    extra=context_unpack(request, {'MESSAGE_ID': 'switched_lot_active.auction'}))
        lot.status = 'active.auction'


def process_lot_status_change(request):
    lot = request.context

    if lot.status == 'pending.deleted' and request.validated['data'].get('status') == 'deleted':
        for auction in lot.auctions:
            auction.status = 'cancelled'
        lot.contracts[0].status = 'cancelled'
    elif lot.status == 'active.salable' and request.validated['data'].get('status') == 'composing':
        lot.rectificationPeriod = None


def process_caravan_contract_report_result(request):
    lot = request.validated['lot']
    contract = request.validated['contract']

    if lot.status == 'active.contracting' and contract.status == 'unsuccessful':
        LOGGER.info('Switched lot %s to %s', lot.id, 'pending.dissolution',
                    extra=context_unpack(request, {'MESSAGE_ID': 'switched_lot_pending.dissolution'}))
        lot.status = 'pending.dissolution'
    elif lot.status == 'active.contracting' and contract.status == 'complete':
        LOGGER.info('Switched lot %s to %s', lot.id, 'pending.sold',
                    extra=context_unpack(request, {'MESSAGE_ID': 'switched_lot_pending.sold'}))
        lot.status = 'pending.sold'


def update_auctions(lot):
    prec = Decimal('0.01')
    auctions = sorted(lot.auctions, key=lambda a: a.tenderAttempts)
    english = auctions[0]
    second_english = auctions[1]
    insider = auctions[2]

    auto_calculated_fields = ['value', 'minimalStep', 'registrationFee', 'guarantee', 'bankAccount']
    auto_calculated_fields = filter(
        lambda f: getattr(english, f, None), auto_calculated_fields
    )

    for auction in (second_english, insider):
        for key in auto_calculated_fields:
            object_class = getattr(lot.__class__.auctions.model_class, key)
            auction[key] = object_class(english[key].serialize())
            if key in ['registrationFee', 'bankAccount']:
                continue
            elif key in ['guarantee']:
                auction[key]['amount'] = (second_english['value']['amount'] / 100).quantize(prec, ROUND_HALF_UP)
            else:
                auction[key]['amount'] = (
                    0 if key == 'minimalStep' and auction.procurementMethodType == 'sellout.insider'
                    else (english[key]['amount'] / 2).quantize(prec, ROUND_HALF_UP)
                )

    insider.tenderingDuration = second_english.tenderingDuration
