.. . Kicking page rebuild 2014-10-30 17:00:08
.. include:: defs.hrst

.. index:: Lot, Period, Date, Decisions 

.. _lot:

Lot
===============

Schema
------

:id:
    string, auto-generated, read-only
    
:lotID:
   string, auto-generated, read-only

   The lot identifier to refer that lot to in the `paper` documentation. 

   |ocdsDescription|
   LotID is included to make the flattened data structure more convenient.

:owner:  
    string, auto-generated, read-only

    The entity whom the lot is owned by.

:date:
    string, auto-generated, read-only
    
    The date of lot creation/undoing.

:title:
    string, multilingual, required
    
    Initial data originates from `asset.title`.

:description:
    string, multilingual, required
    
    |ocdsDescription|
    A description of the goods, services to be provided.
    
    Initial data originates from `asset.description`.
    
:dateModified:    
    string, auto-generated, read-only
    
    |ocdsDescription|
    Date when the lot was last modified.

:status:
    string, required
    
    The lot status within the Registry.

:assets:
    string, required
    
    id of the related asset. Id of the one asset only can be noted.
    
:decisions:
    Array of :ref:`Decisions`, required

    Also include the data from `asset.decisions <http://assetsbounce.api-docs.registry.ea2.openprocurement.io/en/latest/standard/asset.html#decisions>`_.
    
:lotCustodian:

   :ref:`Organization`, required

   An entity managing the lot. Initial data originates from `asset.assetCustodian <http://assetsbounce.api-docs.registry.ea2.openprocurement.io/en/latest/standard/organization.html#organization>`_.

:items:
    :ref:`Item`, required

    Initial data originates from `asset.items <http://assetsbounce.api-docs.registry.ea2.openprocurement.io/en/latest/standard/item.html>`_.

:lotHolder:
   :ref:`Organization`, required

   Initial data originates from `asset.assetHolder <http://assetsbounce.api-docs.registry.ea2.openprocurement.io/en/latest/standard/organization.html#organization>`_.

:rectificationPeriod:
    :ref:`Period`, auto-generated, read-only

    Period during which the lot's owner can edit it.

:auctions:
    :ref:`Auctions`, required

    Auction conditions due to which the lot is to be sold.
    
:documents:
    Array of :ref:`documents` objects
 
    |ocdsDescription|
    All documents and attachments related to the lot.

:mode:
    optional

    The additional parameter with a value `test`.

:lotType:
    string, auto-generated, read-only

    Type of the given lot. Given value:

    * `yoke` - lotType for the small scale privatization process.

.. _period:    

Period
======

Schema
------

:startDate:
    string, :ref:`Date`

    |ocdsDescription|
    The start date for the period.
    `startDate` should always precede `endDate`.

:endDate:
    string, :ref:`Date`

    |ocdsDescription|
    The end date for the period.

.. _date:

Date
====

Date/time in `ISO 8601 <https://en.wikipedia.org/wiki/ISO_8601#Dates>`_.


.. _value:

Value
===============

Schema
------

:amount:    
    float, required

    Should be positive.
    
:currency:
    string, required
    
    |ocdsDescription|
    The currency in 3-letter ISO 4217 format.
    
:valueAddedTaxIncluded:
    bool, required


.. _decisions:

Decisions
=========

Schema
------

:title:
    string, multilingual, optional
    
    * Ukrainian by default (optional) - Ukrainian title
    
    * ``title_en`` (English) - English title
    
    * ``title_ru`` (Russian) - Russian title

:decisionDate:
    :ref:`Date`, required

    |ocdsDescription|
    The date on which the document was first published.

:decisionID:
    string, required

    The decision identifier to refer to in the `paper` documentation.

:decisionOf:
    string, required

    Possible values are:

    * `lot`
    * `asset`

:relatedItem:
    string, optional

    ID of related asset.