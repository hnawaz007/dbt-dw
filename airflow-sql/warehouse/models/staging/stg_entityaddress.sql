with source as (

    select * from {{ source('adventureworks', 'BusinessEntityAddress') }}
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