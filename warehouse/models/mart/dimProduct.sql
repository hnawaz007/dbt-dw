select
    {{ dbt_utils.generate_surrogate_key(['stg_product.productid']) }} as product_key,
    stg_product.productid,
    stg_product.productname as product_name,
    stg_product.productnumber,
    stg_product.color,
    stg_product.daystomanufacture,
	stg_product.safetystocklevel,
    stg_product.standardcost,
    stg_productsubcategory.productsubcategory as product_subcategory_name,
    stg_productcategory.productcategory as product_category_name,
    stg_product.sellstartdate,
    stg_product.sellenddate
from  {{ ref('stg_product') }}
left join  {{ ref('stg_productsubcategory') }} on stg_product.productsubcategoryid = stg_productsubcategory.productsubcategoryid
left join  {{ ref('stg_productcategory') }} on stg_productsubcategory.productcategoryid = stg_productcategory.productcategoryid