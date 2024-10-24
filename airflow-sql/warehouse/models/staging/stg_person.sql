with source as (

    select * from {{ source('adventureworks', 'vw_person') }}
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
        gender,
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