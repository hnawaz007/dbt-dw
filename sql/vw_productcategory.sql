USE [AdventureWorks2019]
GO

/****** Object:  View [dbo].[vw_productcategory]    Script Date: 6/3/2023 10:48:44 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

/****** Script for SelectTopNRows command from SSMS  ******/

CREATE View [dbo].[vw_productcategory]
AS
SELECT [ProductCategoryID]
      ,cast([Name] as varchar(50)) AS ProductCategory
      ,[rowguid]
      ,[ModifiedDate]
  FROM [AdventureWorks2019].[Production].[ProductCategory]
GO


