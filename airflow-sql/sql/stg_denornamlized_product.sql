create table if not exists stg_denormalized_products as (
    SELECT 
	   ps.productsubcategory 
	  ,pc.productcategory 
	  ,p.ProductID
      ,p.productname
      ,p.productnumber
      ,p.productline
      ,p.color
      ,p.safetystocklevel
      ,p.reorderpoint
      ,p.standardcost
      ,p.listprice
      ,p."Size" as size
      ,p.sizeunitmeasurecode
      ,p.daystomanufacture
      ,p."Class" as class
      ,p."Style" as style
      ,p.productmodelid
      ,p.sellstartdate
      ,p.sellenddate
      ,p.discontinueddate
      ,p.modifieddate
  FROM staging.stg_product p
  left join staging.stg_productsubcategory ps on p.productsubcategoryid = ps.productsubcategoryid
  left join staging.stg_productcategory pc on ps.productcategoryid = pc.productcategoryid
)
