with source as (

    select * from {{ source('src_postgres', 'salesorderheadersalesreason') }}
),
renamed as (

    select 
        modifieddate,
        salesorderid,
        salesreasonid
    from source
)

select * from renamed