with source as (

    select * from {{ source('src_postgres', 'vw_person') }}
),
renamed as (

    select 
        title,
        suffix,
        rowguid,
        lastname,
        firstname,
        middlename,
        persontype,
        demographics,
        modifieddate,
        emailpromotion,
        businessentityid,
        additionalcontactinfo
    from source
)

select * from renamed