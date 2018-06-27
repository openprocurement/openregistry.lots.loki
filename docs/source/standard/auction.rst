.. . Kicking page rebuild 2014-10-30 17:00:08
.. include:: defs.hrst

.. index:: Auction, Duration, Value, Guarantee, auctionParameters, Bank Account, Сontracts

.. _auction:

Auction
=======

Schema
------

:id:
  string, auto-generated, read-only

:auctionID:
  string, auto-generated, read-only

  The auction identifier to refer auction to in "paper" documentation. 

  |ocdsDescription|
  It is included to make the flattened data structure more convenient.
   
:procurementMethodType:
  string, auto-generated, read-only

  Type that defines what type of the procedure is going to be used. Possible values:

  * `sellout.english` - procedure with the open ascending price auction;

  * `sellout.insider` - procedure with the insider auction.

:procurementMethodDetails:
  string, optional 

  Parameter that accelerates auction periods. Set *quick, accelerator=1440* as text value for `procurementMethodDetails` for the time frames to be reduced in 1440 times.

:submissionMethodDetails:
  string, optional 

  Parameter that works only with mode = "test" and speeds up auction start date. 

  Possible values are:

  * `quick(mode:no-auction)`; 
  * `quick(mode:fast-forward)`.

:sandboxParameters:
  string, optional

  Parameter that accelerates lot periods. Set quick, accelerator=1440 as text value for `sandboxParameters` for the time frames to be reduced in 1440 times.

:auctionPeriod:
  :ref:`period`, required

  Period when the first auction is conducted. Here only `startDate` has be provided.

:tenderingDuration:
  :ref:`Duration`, required

  Duration of tenderPeriod for 2nd and 3rd procedures within the privatization cycle. 

:documents:
  Array of :ref:`documents` objects
 
  |ocdsDescription|
  All documents and attachments related to the auction.

:value:
  :ref:`value`, required

  Total available budget of the 1st auction. Bids lower than ``value`` will be rejected.

  `Auction.value` for 2nd and 3rd auctions within the privatization cycle will be calculated as half of the `auction.value` provided.

  |ocdsDescription|
  The total estimated value of the procurement.

:guarantee:
  :ref:`Guarantee`, required

  Bid guarantee. `Lots.auctions.guarantee` for 2nd and 3rd auctions within the privatization cycle will be calculated auctomatically.

:registrationFee:
  :ref:`Guarantee`, required

  Bid registration fee. `Lots.auctions.registrationFee` for 2nd and 3rd auctions within the privatization cycle will be calculated auctomatically.

:minimalStep:
  :ref:`value`, required

  The minimal step of the 1st auction. `Lots.auctions.minimalStep` for 2nd and 3rd auctions within the privatization cycle will be calculated auctomatically.

:auctionParameters:
  :ref:`auctionParameters`, optional

  Parameters for the auction to be held.

  Ogranizator can optionally set value for the 3rd auction within the `lots.auctions` structure.

:bankAccount:
  :ref:`bankAccount`, required

  Details which uniquely identify a bank account, and are used when making or receiving a payment.

:tenderAttempts: 
  integer, auto-generated, read-only

  The number which represents what time (from 1 up to 3) procedure with a current lot takes place.
  
:status: 
  string, required

  Auction status within which the lot is being sold:
  
  * `scheduled` - the process is planned, but is not yet taking place. Details of the anticipated dates may be provided further;
  
  * `active` -  the process is currently taking place;  
  
  * `complete` - the process is complete; 
  
  * `cancelled` - the process has been cancelled;  

  * `unsuccessful` - the process has been unsuccessful.

:contracts:
  Array of :ref:`contracts`, auto-generated, read-only

  Information of the related contract.

:relatedProcessID:
  string, required

  Internal id of the auction.

.. _auctionParameters:

Auction Parameters
==================

Schema
------

:type:
  string, auto-generated, read-only

  Type of the auction.

:dutchSteps:
  integer, optional

  Number of steps within the dutch part of the insider auction. 

  Possible values are [1; 100]. Defaul value is 99.

.. _duration:

Duration
========

Duration in `ISO 8601 <https://en.wikipedia.org/wiki/ISO_8601#Durations>`_.

.. _value:

Value
=====

Schema
------

:amount:    
  float, required

  Should be positive.

  |ocdsDescription|
  Amount as a number.
    
:currency:
  string, required
    
  |ocdsDescription|
  The currency in 3-letter ISO 4217 format.
    
:valueAddedTaxIncluded:
  bool, required

  Possible values are `true` or `false`.

.. _guarantee:

Guarantee
=========

Schema
------

:amount:    
  float, required

  Should be positive.

  |ocdsDescription|
  Amount as a number.
    
:currency:
  string, required
    
  |ocdsDescription|
  The currency in 3-letter ISO 4217 format.

.. _bankAccount:

Bank Account
============

Schema
------

:description:
  string, multilingual, optional
    
  Additional information that has to be noted from the Organizator's point.

:bankName:
  string, required

  Name of the bank.

:accountIdentification:
  Array of :ref:`Classification`, required

  Major data on the account details of the state entity selling a lot, to facilitate payments at the end of the process.

  Most frequently used are:

  * `UA-EDR`; 
  * `UA-MFO`;
  * `accountNumber`.

.. _contracts:

Сontracts
=========

All of the fields within are auto-generated & read-only

Schema
------

:type:
  string, required, auto-generated, read-only

  Type of the contract. The only value is `yoke`.

:contractID:
  string, required, auto-generated, read-only

  The contract identifier to refer to in “paper” documentation.

  Added as long as the contract is being created within the Module of Contracting.

:relatedProcessID:
  string, required, auto-generated, read-only

  Internal identifier of the object within the Module of Contracting.

  Added as long as the contract is being created within the Module of Contracting.