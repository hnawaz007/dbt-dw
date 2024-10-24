with source as (

    select * from {{ source('adventureworks', 'vw_stateprovince') }}
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