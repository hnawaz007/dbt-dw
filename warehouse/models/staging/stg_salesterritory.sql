with source as (

    select * from {{ source('src_postgres', 'vw_salesterritory') }}
),
renamed as (

    select 
        "Group",
        costytd,
        rowguid,
        salesytd,
        territoryid,
        costlastyear,
        modifieddate,
        saleslastyear,
        countryregioncode,
        salesterritoryname
    from source
)

select * from renamed