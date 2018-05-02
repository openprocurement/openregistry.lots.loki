# -*- coding: utf-8 -*-
from uuid import uuid4
from copy import deepcopy
from pyramid.security import Allow
from schematics.exceptions import ValidationError
from schematics.types import StringType, IntType, MD5Type
from schematics.types.compound import ModelType, ListType
from schematics.types.serializable import serializable
from zope.interface import implementer
from openregistry.lots.core.constants import (
    SANDBOX_MODE,
)

from openregistry.lots.core.models import (
    Classification,
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
    Value

)

from openregistry.lots.core.models import ILot, Lot as BaseLot
from openregistry.lots.core.utils import (
    get_now,
    calculate_business_date
)

from .constants import (
    LOT_STATUSES,
    AUCTION_STATUSES
)
from .roles import (
    lot_roles,
    auction_roles,
    auctionParameters_roles
)


class ILokiLot(ILot):
    """ Marker interface for basic lots """


class StartDateRequiredPeriod(Period):
    startDate = IsoDateTimeType(required=True)


class UAEDRAndMFOClassification(Classification):
    scheme = StringType(choices=['UA-EDR', 'MFO', 'accountNumber'], required=True)


class AccountDetails(Model):
    description = StringType()
    bankName = StringType()
    accountNumber = StringType()
    accountCodes = ListType(ModelType(UAEDRAndMFOClassification), default=list())


class AuctionParameters(Model):
    class Options:
        roles = auctionParameters_roles

    type = StringType(choices=['english', 'insider'])
    dutchSteps = IntType(default=None, min_value=1, max_value=100)


class Auction(Model):
    class Options:
        roles = auction_roles

    id = StringType(required=True, min_length=1, default=lambda: uuid4().hex)
    auctionID = StringType()
    status = StringType(choices=AUCTION_STATUSES)
    procurementMethodType = StringType(choices=['sellout.english', 'sellout.insider'])
    tenderAttempts = IntType(min_value=1, max_value=3)
    auctionPeriod = ModelType(StartDateRequiredPeriod)
    value = ModelType(Value)
    minimalStep = ModelType(Value)
    guarantee = ModelType(Guarantee)
    registrationFee = ModelType(Guarantee)
    accountDetails = ModelType(AccountDetails)
    auctionParameters = ModelType(AuctionParameters)
    tenderingDuration = IsoDurationType()
    submissionMethodDetails = StringType()
    submissionMethodDetails_en = StringType()
    submissionMethodDetails_ru = StringType()
    if SANDBOX_MODE:
        procurementMethodDetails = StringType()

    def get_role(self):
        root = self.__parent__.__parent__
        request = root.request
        if request.authenticated_role == 'Administrator':
            role = 'Administrator'
        elif request.authenticated_role == 'convoy':
            role = 'convoy'
        else:
            role = 'edit_{}.{}'.format(request.context.tenderAttempts, request.context.procurementMethodType)
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
    items = ListType(ModelType(Item), default=list())
    documents = ListType(ModelType(Document), default=list())
    decisions = ListType(ModelType(Decision), default=list(), min_size=1, max_size=2, required=True)
    assets = ListType(MD5Type(), required=True, min_size=1, max_size=1)
    auctions = ListType(ModelType(Auction), default=list(), max_size=3)

    def get_role(self):
        root = self.__parent__
        request = root.request
        if request.authenticated_role == 'Administrator':
            role = 'Administrator'
        elif request.authenticated_role == 'concierge':
            role = 'concierge'
        elif request.authenticated_role == 'convoy':
            role = 'convoy'
        else:
            after_rectificationPeriod = bool(
                request.context.rectificationPeriod and
                request.context.rectificationPeriod.endDate < get_now()
            )
            if request.context.status == 'pending' and after_rectificationPeriod:
                return 'edit_pendingAfterRectificationPeriod'
            role = 'edit_{}'.format(request.context.status)
        return role

    def validate_auctions(self, data, value):
        if not value:
            return

        # Use the first two auction because they must be english auctions
        # because of strict order(english, english, insider)
        for auction in value[:2]:
            if auction.auctionParameters and auction.auctionParameters.dutchSteps:
                raise ValidationError('dutchSteps can be filled only when procurementMethodType is Loki.insider.')

        if value[0].tenderingDuration:
            raise ValidationError('First loki.english have no tenderingDuration.')
        if not all(auction.tenderingDuration for auction in value[1:]):
            raise ValidationError('tenderingDuration is required for second loki.english and loki.insider.')
        if value[1].tenderingDuration != value[2].tenderingDuration:
            raise ValidationError('tenderingDuration for second loki.english and loki.insider should be the same.')

    @serializable(serialized_name='auctions', serialize_when_none=False)
    def serialize_auctions(self):
        self.auctions[0]['procurementMethodType'] = 'Loki.english'
        self.auctions[1]['procurementMethodType'] = 'Loki.english'
        self.auctions[2]['procurementMethodType'] = 'Loki.insider'

        auto_calculated_fields = ['value', 'minimalStep', 'registrationFee', 'guarantee']
        for i in range(1, 3):
            for key in auto_calculated_fields:
                object_class = self.auctions[0][key].__class__
                self.auctions[i][key] = object_class(self.auctions[0][key].serialize())
                self.auctions[i][key]['amount'] = self.auctions[0][key]['amount'] / 2


    @serializable(serialized_name='rectificationPeriod', serialize_when_none=False)
    def serialize_rectificationPeriod(self):
        if self.status == 'pending' and not self.rectificationPeriod:
            self.rectificationPeriod = type(self).rectificationPeriod.model_class()
            self.rectificationPeriod.startDate = get_now()
            self.rectificationPeriod.endDate = calculate_business_date(self.rectificationPeriod.startDate,
                                                                       RECTIFICATION_PERIOD_DURATION,
                                                                       None)
    @serializable(serialize_when_none=False, serialized_name='auctions', type=ListType(ModelType(Auction)))
    def auctions_serialize(self):
        if self.auctions:
            auto_calculated_fields = ['value', 'minimalStep', 'registrationFee', 'guarantee']
            auctions = sorted(self.auctions, key=lambda a: a.tenderAttempts)
            english = auctions[0]
            second_english = auctions[1]
            insider = auctions[2]
            auto_calculated_fields = filter(
                lambda f: getattr(english, f, None), auto_calculated_fields
            )
            for auction in (second_english, insider):
                for key in auto_calculated_fields:
                    object_class = getattr(self.__class__.auctions.model_class, key)
                    auction[key] = object_class(english[key].serialize())
                    auction[key]['amount'] = english[key]['amount'] / 2

            insider.tenderingDuration = second_english.tenderingDuration
        return self.auctions

    def __acl__(self):
        acl = [
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_lot'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_lot_documents'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_lot_items'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_lot_auctions'),
        ]
        return acl
