USE [AdventureWorks2019]
GO

/****** Object:  View [dbo].[vw_salesorderheader]    Script Date: 7/28/2023 10:58:57 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

/****** Script for SelectTopNRows command from SSMS  ******/
create view [dbo].[vw_salesorderheader]
as
SELECT [SalesOrderID]
      ,[RevisionNumber]
      ,[OrderDate]
      ,[DueDate]
      ,[ShipDate]
      ,[Status]
      ,case when [OnlineOrderFlag] = 1 
			then 'Y'
			else 'N'
			end as [OnlineOrderFlag]
      ,[SalesOrderNumber]
      ,cast([PurchaseOrderNumber] as varchar(25)) as [PurchaseOrderNumber]
      ,cast([AccountNumber] as varchar(15)) as [AccountNumber]
      ,[CustomerID]
      ,[SalesPersonID]
      ,[TerritoryID]
      ,[BillToAddressID]
      ,[ShipToAddressID]
      ,[ShipMethodID]
      ,[CreditCardID]
      ,[CreditCardApprovalCode]
      ,[CurrencyRateID]
      ,[SubTotal]
      ,[TaxAmt]
      ,[Freight]
      ,[TotalDue]
      ,[Comment]
      ,[rowguid]
      ,[ModifiedDate]
  FROM [AdventureWorks2019].[Sales].[SalesOrderHeader]
GO
