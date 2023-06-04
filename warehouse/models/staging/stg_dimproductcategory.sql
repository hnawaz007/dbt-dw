
with source_data as (

    select * from {{ source( 'src_postgres', 'vw_productcategory' ) }}

)

select 
    	productcategoryid, 
		productcategory
from source_data
