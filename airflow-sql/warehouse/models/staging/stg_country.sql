with source as (

    select * from {{ source('adventureworks', 'vw_countryregion') }}
),

isocountry as (

    select * from {{ ref('country_codes') }}
),
renamed as (

    select 
        modifieddate,
        countryregioncode,
        countryregionname
    from source
),
isorename as (

    select 
        "Alpha-2 code" as isocode2,
        "Alpha-3 code" as isocode3,
        "Numeric" as uncode
    from isocountry
)

select 
        modifieddate,
        countryregioncode,
        countryregionname,
        isocode3,
        uncode
from renamed
left join isorename on isorename.isocode2 = renamed.countryregioncode