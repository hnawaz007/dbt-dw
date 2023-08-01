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
        modifieddate,
        emailpromotion,
        businessentityid,
        houseownerflag, 
        occupation, 
        maritalstatus, 
        commutedistance, 
        education, 
        numbercarsowned, 
        totalchildren, 
        birthdate, 
        datefirstpurchase
    from source
)

select * from renamed