# -*- coding: utf-8 -*-
from uuid import uuid4
from pyramid.security import Allow
from schematics.types import StringType, IntType, MD5Type, FloatType
from schematics.exceptions import ValidationError
from schematics.types.compound import ModelType, ListType
from schematics.types.serializable import serializable
from zope.interface import implementer
from openregistry.lots.core.constants import (
    SANDBOX_MODE,
)

from openregistry.lots.core.models import (
    LokiDocument as Document,
    LokiItem as Item,
    Decision,
    AssetCustodian,
    AssetHolder,
    Model,
    IsoDateTimeType,
    IsoDurationType,
    Guarantee,
    Period,
    Value,
    BankAccount,
    AuctionParameters
)

from openregistry.lots.core.validation import validate_items_uniq
from openregistry.lots.core.models import (
    ILot,
    Lot as BaseLot,
    get_lot
)
from openregistry.lots.core.utils import (
    get_now,
    calculate_business_date
)

from .constants import (
    LOT_STATUSES,
    AUCTION_STATUSES,
    AUCTION_DOCUMENT_TYPES,
    DEFAULT_REGISTRATION_FEE,
    DAYS_AFTER_RECTIFICATION_PERIOD
)
from .roles import (
    lot_roles,
    auction_roles,
    decision_roles,
    auction_period_roles,
    contracts_roles
)


class ILokiLot(ILot):
    """ Marker interface for basic lots """


class StartDateRequiredPeriod(Period):
    class Options:
        roles = auction_period_roles
    startDate = IsoDateTimeType(required=True)


class AuctionDocument(Document):
    documentType = StringType(choices=AUCTION_DOCUMENT_TYPES, required=True)
    documentOf = StringType(choices=['auction'])


class RegistrationFee(Guarantee):
    amount = FloatType(min_value=0, default=DEFAULT_REGISTRATION_FEE)


class LotDecision(Decision):
    class Options:
        roles = decision_roles
    decisionOf = StringType(choices=['lot', 'asset'], default='lot')


class Auction(Model):
    class Options:
        roles = auction_roles

    id = StringType(required=True, min_length=1, default=lambda: uuid4().hex)
    auctionID = StringType()
    relatedProcessID = StringType()
    status = StringType(choices=AUCTION_STATUSES)
    procurementMethodType = StringType(choices=['sellout.english', 'sellout.insider'])
    tenderAttempts = IntType(min_value=1, max_value=3)
    auctionPeriod = ModelType(StartDateRequiredPeriod)
    value = ModelType(Value)
    minimalStep = ModelType(Value)
    guarantee = ModelType(Guarantee)
    registrationFee = ModelType(RegistrationFee, default={})
    bankAccount = ModelType(BankAccount)
    documents = ListType(ModelType(AuctionDocument), default=list())
    auctionParameters = ModelType(AuctionParameters)
    tenderingDuration = IsoDurationType()
    submissionMethodDetails = StringType()
    submissionMethodDetails_en = StringType()
    submissionMethodDetails_ru = StringType()
    if SANDBOX_MODE:
        procurementMethodDetails = StringType()

    def validate_minimalStep(self, data, value):
        if value and value.amount and data.get('value'):
            if data.get('value').amount < value.amount:
                raise ValidationError(u"value should be less than value of auction")
            if data.get('value').currency != value.currency:
                raise ValidationError(u"currency should be identical to currency of value of auction")
            if data.get('value').valueAddedTaxIncluded != value.valueAddedTaxIncluded:
                raise ValidationError(
                    u"valueAddedTaxIncluded should be identical to valueAddedTaxIncluded of value of auction")

    def validate_auctionPeriod(self, data, period):
        lot = get_lot(data['__parent__'])
        if data['tenderAttempts'] == 1 and lot.rectificationPeriod:
            min_auction_start_date = calculate_business_date(
                start=lot.rectificationPeriod.endDate,
                delta=DAYS_AFTER_RECTIFICATION_PERIOD,
                context=lot,
                working_days=True
            )
            if min_auction_start_date > period['startDate']:
                raise ValidationError(
                    'startDate of auctionPeriod must be at least '
                    'in {} days after endDate of rectificationPeriod'.format(DAYS_AFTER_RECTIFICATION_PERIOD.days)
                )

    def get_role(self):
        root = self.__parent__.__parent__
        request = root.request
        if request.authenticated_role == 'Administrator':
            role = 'Administrator'
        elif request.authenticated_role == 'convoy':
            role = 'convoy'
        elif request.authenticated_role == 'concierge':
            role = 'concierge'
        else:
            role = 'edit_{}.{}'.format(request.context.tenderAttempts, request.context.procurementMethodType)
        return role


class Contract(Model):
    class Options:
        roles = contracts_roles

    id = StringType(required=True, min_length=1, default=lambda: uuid4().hex)
    contractID = StringType()
    relatedProcessID = StringType()
    type = StringType()

    def get_role(self):
        root = self.__parent__.__parent__
        request = root.request
        if request.authenticated_role == 'caravan':
            role = 'caravan'
        elif request.authenticated_role == 'convoy':
            role = 'convoy'
        return role


@implementer(ILokiLot)
class Lot(BaseLot):
    class Options:
        roles = lot_roles

    title = StringType()
    status = StringType(choices=LOT_STATUSES, default='draft')
    description = StringType()
    lotType = StringType(default="loki")
    rectificationPeriod = ModelType(Period)
    lotCustodian = ModelType(AssetCustodian, serialize_when_none=False)
    lotHolder = ModelType(AssetHolder, serialize_when_none=False)
    officialRegistrationID = StringType(serialize_when_none=False)
    items = ListType(ModelType(Item), default=list(), validators=[validate_items_uniq])
    documents = ListType(ModelType(Document), default=list())
    decisions = ListType(ModelType(LotDecision), default=list(), min_size=1, max_size=2, required=True)
    assets = ListType(MD5Type(), required=True, min_size=1, max_size=1)
    auctions = ListType(ModelType(Auction), default=list(), max_size=3)
    contracts = ListType(ModelType(Contract), default=list())
    _internal_type = 'loki'

    def get_role(self):
        root = self.__parent__
        request = root.request
        if request.authenticated_role == 'Administrator':
            role = 'Administrator'
        elif request.authenticated_role == 'concierge':
            role = 'concierge'
        elif request.authenticated_role == 'convoy':
            role = 'convoy'
        elif request.authenticated_role == 'chronograph':
            role = 'chronograph'
        elif request.authenticated_role == 'caravan':
            role = 'caravan'
        else:
            after_rectificationPeriod = bool(
                request.context.rectificationPeriod and
                request.context.rectificationPeriod.endDate < get_now()
            )
            if request.context.status == 'pending' and after_rectificationPeriod:
                return 'edit_pendingAfterRectificationPeriod'
            role = 'edit_{}'.format(request.context.status)
        return role

    @serializable(serialize_when_none=False, type=IsoDateTimeType())
    def next_check(self):
        checks = []
        if self.rectificationPeriod and self.status == 'pending':
            checks.append(self.rectificationPeriod.endDate)
        return min(checks) if checks else None

    def __acl__(self):
        acl = [
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_lot'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_lot_documents'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_lot_items'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_lot_auctions'),
            (Allow, 'g:concierge', 'upload_lot_auctions'),
            (Allow, 'g:convoy', 'upload_lot_auctions'),
            (Allow, 'g:caravan', 'upload_lot_contracts'),
            (Allow, 'g:convoy', 'upload_lot_contracts'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_lot_auction_documents'),
        ]
        return acl
