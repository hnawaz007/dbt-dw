SELECT 
	productid as product_id, 
	productname as name, 
	productnumber as product_number, 
	safetystocklevel as safety_stock_level, 
	reorderpoint as reorder_point, 
	standardcost as standard_cost, 
	listprice as list_price, 
	daystomanufacture as days_to_manufacture, 
	modifieddate as modified_date
--into staging.product
	FROM staging.stg_product
limit 10;

