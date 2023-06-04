USE [AdventureWorks2019]
GO

/****** Object:  View [dbo].[vw_stateprovince]    Script Date: 6/3/2023 10:49:56 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

/****** Script for SelectTopNRows command from SSMS  ******/
Create View [dbo].[vw_stateprovince]
AS

SELECT [StateProvinceID]
      ,[StateProvinceCode]
      ,[CountryRegionCode]
      ,[IsOnlyStateProvinceFlag]
      ,cast([Name] as varchar(50)) AS StatProvinceName
      ,[TerritoryID]
      ,[rowguid]
      ,[ModifiedDate]
  FROM [AdventureWorks2019].[Person].[StateProvince]
GO


