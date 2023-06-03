# dbt build a datawarehouse using dimensional modeling
This is a dbt repo. We build a practical datawarehouse using Kimball dimensional model with dbt. 

We use a transactional database, SQL Server, [AdventureWorks2019](https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure?view=sql-server-ver16&tabs=ssms) as our source. We extract and load data with an EL tool [Airbyte](https://www.youtube.com/watch?v=2FvMa7vaxDY&t).

You can setup SQL Server's environment using the [following guidelines](https://www.youtube.com/watch?v=e5mvoKuV3xs&t=6s)
PostgreSQL setup guide [link](https://www.youtube.com/watch?v=fjYiWXHI7Mo)
dbt setup [guide](https://www.youtube.com/watch?v=gH1w4OIgXj4)

Using dbt we transform this data into dimensions and facts. 


## Source tables/views used from AdventureWorks datatabase
| schemaname 	| tablename                   	| type  	|
|------------	|-----------------------------	|-------	|
| source     	| address                     	| table 	|
| source     	| customer                    	| table 	|
| source     	| salesorderdetail            	| table 	|
| source     	| salesorderheadersalesreason 	| table 	|
| source     	| salesorderheader            	| table 	|
| source     	| vw_countryregion            	| view  	|
| source     	| vw_product                  	| view  	|
| source     	| vw_productcategory          	| view  	|
| source     	| vw_person                   	| view  	|
| source     	| vw_store                    	| view  	|
| source     	| vw_salesreason              	| view  	|
| source     	| vw_salesterritory           	| view  	|
| source     	| vw_productsubcategory       	| view  	|
| source     	| vw_stateprovince            	| view  	|

