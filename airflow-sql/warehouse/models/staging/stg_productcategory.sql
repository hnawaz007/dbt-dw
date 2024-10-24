with source as (

    select * from {{ source('adventureworks', 'vw_productcategory') }}
),
renamed as (

    select 
        rowguid,
        modifieddate,
        productcategory,
        productcategoryid
    from source
)

select * from renamed