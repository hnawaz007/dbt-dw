create table if not exists source.products as (
    SELECT 
	   ps.englishproductsubcategoryname AS productsubcategoryname
	  ,pc.englishproductcategoryname AS productcategoryname
	  ,p.productkey
      ,p.englishproductname AS productname
      ,p.productline
      ,p.modelname
      ,p.finishedgoodsflag
      ,p.color
      ,p."safetystocklevel"
      ,p."reorderpoint"
      ,p."standardcost"
      ,p."listprice"
      ,p."Size" AS size
      ,p."sizeunitmeasurecode"
      ,p."weightunitmeasurecode"
      ,p."weight"
      ,p."daystomanufacture"
      ,p."Class" AS class
      ,p."Style" AS style
	    ,p._airbyte_emitted_at
      ,p._airbyte_normalized_at
  FROM source.src_dimproduct p
  left join source.src_dimproductsubcategory ps on p."productsubcategorykey" = ps."productsubcategorykey"
  left join source.src_dimproductcategory pc on ps."productcategorykey" = pc."productcategorykey"
) 