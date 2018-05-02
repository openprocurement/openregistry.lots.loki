# -*- coding: utf-8 -*-
from pyramid.events import subscriber
from openregistry.lots.core.events import LotInitializeEvent
from openregistry.lots.core.constants import SANDBOX_MODE
from openprocurement.api.utils import get_now

from openregistry.lots.loki.constants import DEFAULT_DUTCH_STEPS

@subscriber(LotInitializeEvent, lotType="loki")
def lot_init_handler(event):
    """ initialization handler for basic lots """
    event.lot.date = get_now()
