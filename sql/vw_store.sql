USE [AdventureWorks2019]
GO

/****** Object:  View [dbo].[vw_store]    Script Date: 6/3/2023 10:50:15 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


Create View [dbo].[vw_store]
AS

SELECT  [BusinessEntityID]
      ,cast([Name] as varchar(50)) AS StatProvinceName
      ,[SalesPersonID]
      ,[Demographics]
      ,[rowguid]
      ,[ModifiedDate]
  FROM [AdventureWorks2019].[Sales].[Store]
GO


