with source as (

    select * from {{ source('src_postgres', 'BusinessEntityAddress') }}
),
renamed as (

    select 
        addresstypeid, 
        businessentityid, 
        modifieddate, 
        addressid
    from source
)

select * from renamed