select
    {{ dbt_utils.generate_surrogate_key(['stg_address.addressid']) }} as address_key,
    stg_address.addressid,
    stg_address.city as city_name,
    stg_address.postalcode, 
    stg_address.addressline1 || ' '|| coalesce(stg_address.addressline2, '') as Addressline,
    stg_stateprovince.statprovincename as state_name,
    stg_countryregion.countryregionname as country_name
from {{ ref('stg_address') }}
left join {{ ref('stg_stateprovince') }} on stg_address.stateprovinceid = stg_stateprovince.stateprovinceid
left join {{ ref('stg_countryregion') }} on stg_stateprovince.countryregioncode = stg_countryregion.countryregioncode