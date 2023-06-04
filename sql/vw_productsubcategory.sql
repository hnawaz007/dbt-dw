USE [AdventureWorks2019]
GO

/****** Object:  View [dbo].[vw_productsubcategory]    Script Date: 6/3/2023 10:49:01 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

/****** Script for SelectTopNRows command from SSMS  ******/
Create View [dbo].[vw_productsubcategory]
AS
SELECT [ProductSubcategoryID]
      ,[ProductCategoryID]
      ,cast([Name] as varchar(50)) AS ProductSubCategory
      ,[rowguid]
      ,[ModifiedDate]
  FROM [AdventureWorks2019].[Production].[ProductSubcategory]
GO


