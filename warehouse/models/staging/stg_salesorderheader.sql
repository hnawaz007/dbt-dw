with source as (

    select * from {{ source('src_postgres', 'vw_salesorderheader') }}
),
renamed as (

    select 
        status,
        onlineorderflag,
        taxamt,
        purchaseordernumber,
        "Comment", --First letter is uppercase therefore in double quoutes
        duedate::timestamp AS duedate,
        freight,
        rowguid,
        shipdate::timestamp AS shipdate,
        subtotal,
        totaldue,
        orderdate::timestamp AS orderdate,
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