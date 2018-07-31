# -*- coding: utf-8 -*-
from openregistry.lots.core.utils import (
    update_logging_context,
    get_now,
    error_handler,
    raise_operation_error,
    get_first_document,
    check_document,
    set_first_document_fields,
    get_type,
    update_document_url,
    calculate_business_date
)
from openregistry.lots.core.validation import (
    validate_data
)
from openregistry.lots.loki.constants import (
    DAYS_AFTER_RECTIFICATION_PERIOD,
    RECTIFICATION_PERIOD_DURATION
)


# Document Validation
def validate_document_data(request, **kwargs):
    context = request.context if 'documents' in request.context else request.context.__parent__
    model = type(context).documents.model_class
    data = validate_data(request, model, "document")
    document = request.validated['document']

    if document.documentType not in (model._document_types_url_only + model._document_types_offline):
        check_document(request, request.validated['document'], 'body')

    first_document = get_first_document(request)

    if first_document:
        set_first_document_fields(request, first_document, document)

    if not document.documentOf:
        document.documentOf = get_type(context).__name__.lower()

    if document.documentType not in (model._document_types_url_only + model._document_types_offline):
        document_route = request.matched_route.name.replace("collection_", "")
        document = update_document_url(request, document, document_route, {})

    request.validated['document'] = document
    return data


def validate_file_upload(request, **kwargs):
    update_logging_context(request, {'document_id': '__new__'})
    if request.registry.use_docservice and request.content_type == "application/json":
        return validate_document_data(request)
    if 'file' not in request.POST or not hasattr(request.POST['file'], 'filename'):
        request.errors.add('body', 'file', 'Not Found')
        request.errors.status = 404
        raise error_handler(request)
    else:
        request.validated['file'] = request.POST['file']


def validate_document_operation_in_not_allowed_lot_status(request, error_handler, **kwargs):
    status = request.validated['lot_status']
    if status not in ['pending', 'composing']:
        raise_operation_error(request, error_handler,
                              'Can\'t update document in current ({}) lot status'.format(status))


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


# Item validation
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


def rectificationPeriod_item_validation(request, error_handler, **kwargs):
    if bool(request.validated['lot'].rectificationPeriod and
            request.validated['lot'].rectificationPeriod.endDate < get_now()):
        request.errors.add('body', 'mode', 'You can\'t change items after rectification period')
        request.errors.status = 403
        raise error_handler(request)


# Decision validation
def validate_decision_by_decisionOf(request, error_handler, **kwargs):
    decision = request.validated['decision']
    if decision.decisionOf != 'lot':
        request.errors.add(
            'body',
            'mode',
            'Can edit only decisions which have decisionOf equal to \'lot\'.'
        )
        request.errors.status = 403
        raise error_handler(request)


# Auction validation
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


def rectificationPeriod_auction_validation(request, error_handler, **kwargs):
    is_rectificationPeriod_finished = bool(
        request.validated['lot'].rectificationPeriod and
        request.validated['lot'].rectificationPeriod.endDate < get_now()
    )

    if request.authenticated_role not in ['convoy', 'concierge'] and is_rectificationPeriod_finished:
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


# Contract validation
def validate_contracts_data(request, error_handler, **kwargs):
    update_logging_context(request, {'auction_id': '__new__'})
    context = request.context if 'auctions' in request.context else request.context.__parent__
    model = type(context).contracts.model_class
    validate_data(request, model)


# Lot validation
def get_fields_errors(required_fields, auction):
    empty_fields = [field for field in required_fields if not auction[field]]

    err_msg = []
    if empty_fields:
        description = {field: ['This field is required.'] for field in empty_fields}
        err_msg.append(description)

    return err_msg


def get_auction_validation_result(lot):
    auctions = sorted(lot.auctions, key=lambda a: a.tenderAttempts)
    english = auctions[0]
    second_english = auctions[1]

    auction_error_message = {
        'location': 'body',
        'name': 'auctions',
        'description': []
    }

    # Get errors from first auction
    required_fields = ['value', 'minimalStep', 'auctionPeriod', 'guarantee', 'bankAccount']
    auction_error_message['description'].extend(get_fields_errors(required_fields, english))

    # Get errors from second auction
    required_fields = ['tenderingDuration']
    auction_error_message['description'].extend(get_fields_errors(required_fields, second_english))

    return auction_error_message


def validate_verification_status(request, error_handler):
    if request.validated['data'].get('status') == 'verification' and request.context.status == 'composing':
        # Decision validation
        if not any(decision.decisionOf == 'lot' for decision in request.context.decisions):
            raise_operation_error(
                        request,
                        error_handler,
                        'Can\'t switch to verification while lot decisions not available.'
                    )

        # Auction validation
        lot = request.validated['lot']
        auctions = sorted(lot.auctions, key=lambda a: a.tenderAttempts)
        english = auctions[0]

        auction_error_message = get_auction_validation_result(lot)

        # Raise errors from first and second auction
        if auction_error_message['description']:
            request.errors.add(**auction_error_message)
            request.errors.status = 422
            raise error_handler(request)

        duration = DAYS_AFTER_RECTIFICATION_PERIOD + RECTIFICATION_PERIOD_DURATION

        min_auction_start_date = calculate_business_date(
            start=get_now(),
            delta=duration,
            context=lot,
            working_days=True
        )

        auction_period = english.auctionPeriod
        if auction_period and min_auction_start_date > auction_period.startDate:
            request.errors.add(
                'body',
                'mode',
                'startDate of auctionPeriod must be '
                'at least in {} days after today'.format(duration.days)
            )
            request.errors.status = 422
            raise error_handler(request)

        if request.errors:
            raise error_handler(request)


def validate_deleted_status(request, error_handler):
    # Moving lot.status to 'deleted' is allowed only when at least one of lot.documents
    # have documentOf = 'cancellationDetails'
    can_be_deleted = any([doc.documentType == 'cancellationDetails' for doc in request.context['documents']])
    if request.json['data'].get('status') == 'pending.deleted' and not can_be_deleted:
        request.errors.add(
            'body',
            'mode',
            "You can set deleted status "
            "only when lot have at least one document with \'cancellationDetails\' documentType")
        request.errors.status = 403
        raise error_handler(request)


def validate_pending_status(request, error_handler):
    # Check if at least one decision with type = 'asset' is available in lot.decisions
    # or patching to pending status is going with decisions
    is_decisions_in_context = any(
        decision.decisionOf == 'asset' for decision in request.context.decisions
    )
    is_decision_in_data = any(
        decision['decisionOf'] == 'asset' for decision in request.validated['data'].get('decisions', [])
    )

    status_check = bool(
        request.json['data'].get('status') == 'pending' and
        request.context.status == 'verification'
    )

    if status_check and not (is_decision_in_data or is_decisions_in_context):
        raise_operation_error(
            request,
            error_handler,
            'Can\'t switch to pending while decisions not available.'
        )

    if status_check and not request.json['data'].get('items', []):
        raise_operation_error(
            request,
            error_handler,
            'Can\'t switch to pending while items in asset not available.'
        )
