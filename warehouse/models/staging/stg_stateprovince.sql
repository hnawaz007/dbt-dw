with source as (

    select * from {{ source('src_postgres', 'vw_stateprovince') }}
),
renamed as (

    select 
        rowguid,
        territoryid,
        modifieddate,
        stateprovinceid,
        statprovincename,
        countryregioncode,
        stateprovincecode
    from source
)

select * from renamed