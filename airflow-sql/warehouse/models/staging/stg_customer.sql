with source as (

    select * from {{ source('adventureworks', 'Customer') }}
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