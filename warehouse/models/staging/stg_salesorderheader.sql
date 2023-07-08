with source as (

    select * from {{ source('src_postgres', 'salesorderheader') }}
),
renamed as (

    select 
        status,
        taxamt,
        "Comment", --First letter is uppercase therefore in double quoutes
        duedate,
        freight,
        rowguid,
        shipdate,
        subtotal,
        totaldue,
        orderdate,
        customerid,
        territoryid,
        creditcardid,
        modifieddate,
        salesorderid,
        shipmethodid,
        salespersonid,
        currencyrateid,
        revisionnumber,
        billtoaddressid,
        shiptoaddressid,
        salesordernumber,
        creditcardapprovalcode
    from source
)

select * from renamed