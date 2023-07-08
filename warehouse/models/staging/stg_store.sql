with source as (

    select * from {{ source('src_postgres', 'vw_store') }}
),
renamed as (

    select 
        rowguid,
        demographics,
        modifieddate,
        salespersonid,
        businessentityid,
        statprovincename
    from source
)

select * from renamed