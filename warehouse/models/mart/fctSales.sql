select
    {{ dbt_utils.generate_surrogate_key(['stg_salesorderdetail.salesorderid', 'salesorderdetailid']) }} as sales_key,
    {{ dbt_utils.generate_surrogate_key(['productid']) }} as product_key,
    {{ dbt_utils.generate_surrogate_key(['customerid']) }} as customer_key,
    {{ dbt_utils.generate_surrogate_key(['creditcardid']) }} as creditcard_key,
    {{ dbt_utils.generate_surrogate_key(['shiptoaddressid']) }} as ship_address_key,
    {{ dbt_utils.generate_surrogate_key(['status']) }} as order_status_key,
    {{ dbt_utils.generate_surrogate_key(['orderdate']) }} as order_date_key,
    {{ dbt_utils.generate_surrogate_key(['shipdate']) }} as ship_date_key,
    {{ dbt_utils.generate_surrogate_key(['duedate']) }} as due_date_key,
    {{ dbt_utils.generate_surrogate_key(['territoryid']) }} as territory_key,
    {{ dbt_utils.ge}}
    orderdate,
    onlineorderflag,
    stg_salesorderdetail.unitpricediscount as unitpricediscount,
    stg_salesorderheader.salesordernumber,
	stg_salesorderdetail.salesorderid,
    stg_salesorderdetail.salesorderdetailid,
    stg_salesorderdetail.unitprice,
    stg_salesorderdetail.orderqty,
    stg_salesorderdetail.linetotal as revenue,
    stg_salesorderdetail.linetotal as salesamount,
    case when stg_salesorderdetail.unitpricediscount > 0
        then stg_salesorderdetail.linetotal * stg_salesorderdetail.unitpricediscount 
        else stg_salesorderdetail.linetotal
        end as totaldiscount,
    stg_salesorderheader.taxamt 
from {{ ref('stg_salesorderdetail') }}
inner join  {{ ref('stg_salesorderheader') }} on stg_salesorderdetail.salesorderid = stg_salesorderheader.salesorderid