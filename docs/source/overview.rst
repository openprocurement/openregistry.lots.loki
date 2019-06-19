Overview
========

openregistry.lots.loki contains the description of the Lots Registry.

Features
--------

* Lot represents the finalized object to be privatized within the process.
* One asset only may be included in a single lot.
* Asset which is included in lot, marked as attached to it and can't be used for other lots formation.
* Lot can be deleted only in case of `documentType: cancellationDetails` has been attached.
* Time for the lot to be edited is `rectificationPeriod`. 

Conventions
-----------

API accepts `JSON <http://json.org/>`_ or form-encoded content in
requests.  It returns JSON content in all of its responses, including
errors.  Only the UTF-8 character encoding is supported for both requests
and responses.

All API POST and PUT requests expect a top-level object with a single
element in it named `data`.  Successful responses will mirror this format. 
The data element should itself be an object, containing the parameters for
the request.

If the request was successful, we will get a response code of `201`
indicating the object was created.  That response will have a data field at
its top level, which will contain complete information on the new lot,
including its ID.

If something went wrong during the request, we'll get a different status
code and the JSON returned will have an `errors` field at the top level
containing a list of problems.  We look at the first one and print out its
message.

---------------------

Project status
--------------

The project has pre alpha status.

The source repository for this project is on GitHub: 
https://github.com/openprocurement/openregistry.lots.loki  

Documentation of related packages
---------------------------------

* `OpenProcurement API <http://api-docs.openprocurement.org/en/latest/>`_
* `Sellout.english  <http://sellout-english.api-docs.ea2.openprocurement.io/en/latest/>`_
* `Sellout.Insider <http://api-docs.openprocurement.org/en/latest/>`_
* `Assets Registry <http://assetsbounce.api-docs.registry.ea2.openprocurement.io/en/latest/>`_
* `Lots Registry for Buyout <http://lotsbargain.api-docs.registry.ea2.openprocurement.io/en/latest/>`_
* `Contracting <http://ceasefire.api-docs.ea2.openprocurement.io/en/latest/>`_

API stability
-------------

API is relatively stable. The changes in the API are communicated via `Open Procurement API
<https://groups.google.com/group/open-procurement-api>`_ maillist.


Next steps
----------
You might find it helpful to look at the :ref:`tutorial`.
