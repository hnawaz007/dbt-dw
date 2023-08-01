with source as (

    select * from {{ source('src_postgres', 'vw_product') }}
),
renamed as (

    select 
        "Size",
        "Class",
        color,
        "Style",
        weight,
        rowguid,
        listprice,
        productid,
        productline,
        productname,
        sellenddate AS sellenddate,
        modifieddate,
        reorderpoint,
        standardcost,
        productnumber,
        sellstartdate AS sellstartdate,
        productmodelid,
        discontinueddate,
        safetystocklevel,
        daystomanufacture,
        sizeunitmeasurecode,
        productsubcategoryid
    from source
)

select * from renamed