.. . Kicking page rebuild 2014-10-30 17:00:08
.. include:: defs.hrst

.. index:: Organization, Company

.. _Organization:

Organization
============

Schema
------

:name:
    string, multilingual, required
    
    Name of the organization.
    
:identifier:
    :ref:`Identifier`, required
    
    The primary identifier for this organization. 
    
:additionalIdentifiers:
    List of :ref:`identifier`, optional
    
:address:
    :ref:`Address`, required for lotCustodian
    
:contactPoint:
    :ref:`ContactPoint`, required for lotCustodian

:additionalContactPoints:
    Array of :ref:`ContactPoint`, optional

:kind:
    string, optional 
    
    Type of the organizer. 
    Available only for lotCustodian.

    Possible values:
        - ``general`` - Organizer (general)
        - ``special`` - Organizer that operates in certain spheres of economic activity
        - ``other`` -  Legal persons that are not organizers in the sense of the Law, but are state, utility, public enterprises, economic partnerships or associations of enterprises in which state or public utility share is 50 percent or more

.. index:: Company, id

.. _Identifier:

Identifier
==========

Schema
------

:scheme:
   string

   |ocdsDescription|
   Organization identifiers be drawn from an existing identification scheme. 
   This field is used to indicate the scheme or codelist in which the
   identifier will be found.  This value should be drawn from the
   Organization Identifier Scheme.

:id:
   string, required
   
   |ocdsDescription| The identifier of the organization in the selected
   scheme.

   The allowed codes are the ones found in `"Organisation Registration Agency"
   codelist of IATI
   Standard <http://iatistandard.org/codelists/OrganisationRegistrationAgency/>`_
   with addition of `UA-EDR` code for organizations registered in Ukraine
   (EDRPOU and IPN).

:legalName:
   string, multilingual

   |ocdsDescription|
   The legally registered name of the organization.
   
   Full legal name (e.g. Nadra Bank).

:uri:
   uri

   |ocdsDescription|
   A URI to identify the organization, such as those provided by Open
   Corporates or some other relevant URI provider.  This is not for listing
   the website of the organization: that can be done through the url field
   of the Organization contact point.


.. index:: Address, City, Street, Country

.. _Address:

Address
=======

Schema
------

:streetAddress:
    string
    
    |ocdsDescription|
    The street address. For example, 1600 Amphitheatre Pkwy.
    
:locality:
    string
    
    |ocdsDescription|
    The locality. For example, Mountain View.
    
:region:
    string
    
    |ocdsDescription|
    The region. For example, CA.
    
:postalCode:
    string
    
    |ocdsDescription|
    The postal code. For example, 94043.
    
:countryName:
    string, multilingual, required
    
    |ocdsDescription|
    The country name. For example, United States.


.. index:: Person, Phone, Email, Website, ContactPoint

.. _ContactPoint:

ContactPoint
============

Schema
------

:name:
    string, multilingual, required
    
    |ocdsDescription|
    The name of the contact person, department, or contact point, for correspondence relating to this contracting process.
    
:email:
    email
    
    |ocdsDescription|
    The e-mail address of the contact point/person.
    
:telephone:
    string
    
    |ocdsDescription|
    The telephone number of the contact point/person. This should include the international dialling code.
    
:faxNumber:
    string, optional
    
    |ocdsDescription|
    The fax number of the contact point/person. This should include the international dialling code.
    
:url:
    URL, optional
    
    |ocdsDescription|
    A web address for the contact point/person.
    

Either `email` or `telephone` field has to be provided.
