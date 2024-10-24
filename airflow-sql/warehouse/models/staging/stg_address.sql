with source as (
    select * from {{ source('adventureworks', 'vw_address') }}
),

renamed as (
    select
        city,
        rowguid,
        addressid,
        postalcode,
        addressline1,
        addressline2,
        modifieddate,
        spatiallocation,
        stateprovinceid
    from source
)

select * from renamed
