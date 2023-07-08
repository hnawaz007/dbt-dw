with source as (

    select * from {{ source('src_postgres', 'vw_productsubcategory') }}
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