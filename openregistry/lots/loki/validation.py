# -*- coding: utf-8 -*-
from openregistry.lots.core.utils import (
    raise_operation_error,
    update_logging_context,
    get_now
)
from openregistry.lots.core.validation import (
    validate_data
)


def validate_document_operation_in_not_allowed_lot_status(request, error_handler, **kwargs):
    status = request.validated['lot_status']
    if status not in ['pending', 'composing']:
        raise_operation_error(request, error_handler,
                              'Can\'t update document in current ({}) lot status'.format(status))


def validate_item_data(request, error_handler, **kwargs):
    update_logging_context(request, {'item_id': '__new__'})
    context = request.context if 'items' in request.context else request.context.__parent__
    model = type(context).items.model_class
    validate_data(request, model, "item")


def validate_patch_item_data(request, error_handler, **kwargs):
    update_logging_context(request, {'item_id': '__new__'})
    context = request.context if 'items' in request.context else request.context.__parent__
    model = type(context).items.model_class
    validate_data(request, model)


def validate_decision_post(request, error_handler):
    if len(request.validated['lot'].decisions) > 1:
        raise_operation_error(request, error_handler,
                              'Can\'t add more than one decisions to lot')


def validate_decision_patch(request, error_handler):
    # Validate second decision because second decision come from asset and can be changed
    is_decisions_available = bool(
        len(request.context.decisions) == 2 or
        len(request.json['data'].get('decisions', [])) == 2
    )
    if request.json['data'].get('status') == 'pending' and not is_decisions_available:
        raise_operation_error(
            request,
            error_handler,
            'Can\'t switch to pending while decisions not available.'
        )

    is_asset_decision_patched_wrong = bool(
        len(request.context.decisions) < 2 or
        (
            request.json['data'].get('decisions') and (
                len(request.json['data']['decisions']) < 2 or
                request.context.decisions[1].serialize() != request.json['data']['decisions'][1]
            )
        )
    )
    if request.context.status == 'pending' and is_asset_decision_patched_wrong:
        raise_operation_error(
            request,
            error_handler,
            'Can\'t update decision that was created from asset')


def rectificationPeriod_item_validation(request, error_handler, **kwargs):
    if bool(request.validated['lot'].rectificationPeriod and
            request.validated['lot'].rectificationPeriod.endDate < get_now()):
        request.errors.add('body', 'mode', 'You can\'t change items after rectification period')
        request.errors.status = 403
        raise error_handler(request)


def rectificationPeriod_document_validation(request, error_handler, **kwargs):
    is_period_ended = bool(
        request.validated['lot'].rectificationPeriod and
        request.validated['lot'].rectificationPeriod.endDate < get_now()
    )
    if bool((is_period_ended and request.validated['document'].documentType != 'cancellationDetails') and
            request.method == 'POST'):
        request.errors.add(
            'body',
            'mode',
            'You can add only document with cancellationDetails after rectification period'
        )
        request.errors.status = 403
        raise error_handler(request)

    if is_period_ended and request.method in ['PUT', 'PATCH']:
        request.errors.add('body', 'mode', 'You can\'t change documents after rectification period')
        request.errors.status = 403
        raise error_handler(request)


def rectificationPeriod_auction_document_validation(request, error_handler, **kwargs):
    is_period_ended = bool(
        request.validated['lot'].rectificationPeriod and
        request.validated['lot'].rectificationPeriod.endDate < get_now()
    )
    if is_period_ended and request.method == 'POST':
        request.errors.add(
            'body',
            'mode',
            'You can\'t add documents to auction after rectification period'
        )
        request.errors.status = 403
        raise error_handler(request)

    if is_period_ended and request.method in ['PUT', 'PATCH']:
        request.errors.add('body', 'mode', 'You can\'t change documents after rectification period')
        request.errors.status = 403
        raise error_handler(request)


def validate_deleted_status(request, error_handler):
    can_be_deleted = any([doc.documentType == 'cancellationDetails' for doc in request.context['documents']])
    if request.json['data'].get('status') == 'pending.deleted' and not can_be_deleted:
        request.errors.add(
            'body',
            'mode',
            "You can set deleted status "
            "only when lot have at least one document with \'cancellationDetails\' documentType")
        request.errors.status = 403
        raise error_handler(request)


def rectificationPeriod_auction_validation(request, error_handler, **kwargs):
    is_rectificationPeriod_finished = bool(
        request.validated['lot'].rectificationPeriod and
        request.validated['lot'].rectificationPeriod.endDate < get_now()
    )
    if request.authenticated_role != 'convoy' and is_rectificationPeriod_finished:
        request.errors.add('body', 'mode', 'You can\'t change auctions after rectification period')
        request.errors.status = 403
        raise error_handler(request)


def validate_auction_data(request, error_handler, **kwargs):
    update_logging_context(request, {'auction_id': '__new__'})
    context = request.context if 'auctions' in request.context else request.context.__parent__
    model = type(context).auctions.model_class
    validate_data(request, model)


def validate_update_auction_in_not_allowed_status(request, error_handler, **kwargs):
    is_convoy_or_concierge = bool(request.authenticated_role in ['convoy', 'concierge'])
    if not is_convoy_or_concierge and request.validated['lot_status'] not in ['draft', 'composing', 'pending']:
            raise_operation_error(
                request,
                error_handler,
                'Can\'t update auction in current ({}) lot status'.format(request.validated['lot_status'])
            )


def validate_update_auction_document_in_not_allowed_status(request, error_handler, **kwargs):
    if request.validated['lot_status'] not in ['draft', 'composing', 'pending']:
            raise_operation_error(
                request,
                error_handler,
                'Can\'t update document of auction in current ({}) lot status'.format(request.validated['lot_status'])
            )


def validate_verification_status(request, error_handler):
    if request.validated['data'].get('status') == 'verification' and request.context.status == 'composing':
        lot = request.validated['lot']
        auctions = sorted(lot.auctions, key=lambda a: a.tenderAttempts)
        english = auctions[0]
        second_english = auctions[1]

        required_fields = ['value', 'minimalStep', 'auctionPeriod', 'guarantee']
        if not all(english[field] for field in required_fields):
            request.errors.add(
                'body',
                'data',
                'Can\'t switch lot to verification status from composing until '
                'these fields are empty {} within the auctions'.format(required_fields)
            )
            request.errors.status = 422

        required_fields = ['tenderingDuration']
        if not all(second_english[field] for field in required_fields):
            request.errors.add(
                'body',
                'data',
                'Can\'t switch lot to verification status from composing until '
                'these fields are empty {} within the second (english) auction'.format(required_fields)
            )
            request.errors.status = 422

        if request.errors:
            raise error_handler(request)
