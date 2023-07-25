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
    stg_person.numbercarsowned, 
    stg_person.totalchildren, 
    stg_person.birthdate, 
    stg_person.datefirstpurchase,
    stg_store.businessentityid as storebusinessentityid,
    stg_store.storename
from {{ ref('stg_customer') }}
left join {{ ref('stg_person') }} on stg_customer.personid = stg_person.businessentityid
left join {{ ref('stg_store') }}on stg_customer.storeid = stg_store.businessentityid
