with source as (

    select * from {{ source('src_postgres', 'vw_countryregion') }}
),
renamed as (

    select 
        modifieddate,
        countryregioncode,
        countryregionname
    from source
)

select * from renamed