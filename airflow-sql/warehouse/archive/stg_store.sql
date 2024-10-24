with source as (

    select * from {{ source('src_postgres', 'vw_store') }}
),
renamed as (

    select 
        rowguid,
        demographics,
        storename,
        modifieddate,
        salespersonid,
        businessentityid
    from source
)

select * from renamed