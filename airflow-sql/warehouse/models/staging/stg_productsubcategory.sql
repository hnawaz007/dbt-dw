with source as (

    select * from {{ source('adventureworks', 'vw_productsubcategory') }}
),
renamed as (

    select 
        rowguid,
        modifieddate,
        productcategoryid,
        productsubcategory,
        productsubcategoryid
    from source
)

select * from renamed