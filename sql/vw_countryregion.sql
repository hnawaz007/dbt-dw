USE [AdventureWorks2019]
GO

/****** Object:  View [dbo].[vw_countryregion]    Script Date: 6/3/2023 10:41:07 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

/****** Script for SelectTopNRows command from SSMS  ******/

Create View [dbo].[vw_countryregion]
AS
SELECT [CountryRegionCode]
      ,cast([Name] as varchar(50)) AS CountryRegionName
      ,[ModifiedDate]
  FROM [AdventureWorks2019].[Person].[CountryRegion]
GO


