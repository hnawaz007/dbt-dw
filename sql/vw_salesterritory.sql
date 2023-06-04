USE [AdventureWorks2019]
GO

/****** Object:  View [dbo].[vw_salesterritory]    Script Date: 6/3/2023 10:49:38 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

/****** Script for SelectTopNRows command from SSMS  ******/
Create View [dbo].[vw_salesterritory]
AS
SELECT [TerritoryID]
      ,cast([Name] as varchar(50)) AS SalesTerritoryName
      ,[CountryRegionCode]
      ,[Group]
      ,[SalesYTD]
      ,[SalesLastYear]
      ,[CostYTD]
      ,[CostLastYear]
      ,[rowguid]
      ,[ModifiedDate]
  FROM [AdventureWorks2019].[Sales].[SalesTerritory]
GO


