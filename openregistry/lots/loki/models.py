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
    SANDBOX_MODE
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
    RECTIFICATION_PERIOD_DURATION,
)
from .roles import (
    lot_roles,
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
    type = StringType(choices=['english', 'insider'])
    dutchSteps = IntType(default=None, min_value=1, max_value=100)
    if SANDBOX_MODE:
        procurementMethodDetails = StringType()


class Auction(Model):
    id = StringType()
    auctionID = StringType()
    procurementMethodType = StringType(choices=['Loki.english', 'Loki.insider'])
    auctionPeriod = ModelType(StartDateRequiredPeriod, required=True)
    tenderingDuration = IsoDurationType()
    documents = ListType(ModelType(Document))
    value = ModelType(Value, required=True)
    minimalStep = ModelType(Value, required=True)
    guarantee = ModelType(Guarantee, required=True)
    registrationFee = ModelType(Guarantee)
    accountDetails = ModelType(AccountDetails)
    auctionParameters = ModelType(AuctionParameters)


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
    auctions = ListType(ModelType(Auction), max_size=3, min_size=3, required=True)

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

    def __acl__(self):
        acl = [
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_lot'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_lot_documents'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_lot_items'),
        ]
        return acl
