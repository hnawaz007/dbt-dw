create table if not exists stg_denormalized_products as (
    SELECT 
	   ps."Name" AS ProductSubcategoryName
	  ,pc."Name" AS ProductCategoryName
	  ,p."ProductID"
      ,p."Name" AS Product_Name
      ,p."ProductNumber"
      ,p."MakeFlag"
      ,p."FinishedGoodsFlag"
      ,p."Color"
      ,p."SafetyStockLevel"
      ,p."ReorderPoint"
      ,p."StandardCost"
      ,p."ListPrice"
      ,p."Size"
      ,p."SizeUnitMeasureCode"
      ,p."WeightUnitMeasureCode"
      ,p."Weight"
      ,p."DaysToManufacture"
      ,p."ProductLine"
      ,p."Class"
      ,p."Style"
      ,p."ProductModelID"
      ,p."SellStartDate"
      ,p."SellEndDate"
      ,p."DiscontinuedDate"
      ,p."ModifiedDate"
  FROM etl.stg_products p
  left join etl.stg_productsubcategory ps on p."ProductSubcategoryID" = ps."ProductSubcategoryID"
  left join etl.stg_productcategory pc on ps."ProductCategoryID" = pc."ProductCategoryID"
)
