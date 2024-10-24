select
    {{ dbt_utils.generate_surrogate_key(['stg_salesorderheader.status']) }} as order_status_key,
    status as order_status,
    case
        when status = 1 then 'in_process'
        when status = 2 then 'approved'
        when status = 3 then 'backordered'
        when status = 4 then 'rejected'
        when status = 5 then 'shipped'
        when status = 6 then 'cancelled'
        else 'no_status'
    end as order_status_name
from  {{ ref('stg_salesorderheader') }}