with source as (

    select * from {{ source('src_postgres', 'vw_salesreason') }}
),
renamed as (

    select 
        salesreason,
        modifieddate,
        salesreasonid
    from source
)

select * from renamed