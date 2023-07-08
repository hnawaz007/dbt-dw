with source as (

    select * from {{ source('src_postgres', 'customer') }}
),
renamed as (

    select 
        storeid,
        rowguid,
        personid,
        customerid,
        territoryid,
        modifieddate,
        accountnumber
    from source
)

select * from renamed