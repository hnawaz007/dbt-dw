with source as (

    select * from {{ source('adventureworks', 'SalesOrderDetail') }}
),
renamed as (

    select 
        rowguid,
        orderqty,
        linetotal,
        productid,
        unitprice,
        modifieddate,
        salesorderid,
        specialofferid,
        unitpricediscount,
        salesorderdetailid,
        carriertrackingnumber
    from source
)

select * from renamed