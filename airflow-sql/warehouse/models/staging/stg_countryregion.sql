with source as (

    select * from {{ source('adventureworks', 'vw_countryregion') }}
),
renamed as (

    select 
        modifieddate,
        countryregioncode,
        countryregionname
    from source
)

select * from renamed