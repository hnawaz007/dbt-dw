select
    {{ dbt_utils.generate_surrogate_key(['stg_customer.customerid']) }} as customer_key,
    stg_customer.customerid,
    stg_person.businessentityid as personbusinessentityid,
    stg_person.title,
    stg_person.firstname || ' '|| lastname as fullname,
    stg_person.houseownerflag, 
    stg_person.occupation, 
    stg_person.maritalstatus, 
    stg_person.commutedistance, 
    stg_person.education, 
    --stg_person.gender,
    stg_person.numbercarsowned, 
    stg_person.totalchildren, 
    stg_person.birthdate, 
    stg_person.datefirstpurchase,
    stg_countryregion.countryregionname as country,
    stg_address.city,
    stg_stateprovince.statprovincename as state,
    stg_address.postalcode,
    stg_address.addressline1,
    stg_address.addressline2
from {{ ref('stg_customer') }}
left join {{ ref('stg_person') }} on stg_customer.personid = stg_person.businessentityid
left join {{ ref('stg_entityaddress') }} on stg_entityaddress.businessentityid = stg_person.businessentityid
left join {{ ref('stg_address') }} on stg_address.addressid = stg_entityaddress.addressid
left join {{ ref('stg_stateprovince') }} on stg_stateprovince.stateprovinceid = stg_address.stateprovinceid
left join {{ ref('stg_countryregion') }} on stg_countryregion.countryregioncode = stg_stateprovince.countryregioncode
where persontype = 'IN'
and addresstypeid = 2