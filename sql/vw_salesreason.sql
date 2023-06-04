USE [AdventureWorks2019]
GO

/****** Object:  View [dbo].[vw_salesreason]    Script Date: 6/3/2023 10:49:23 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

/****** Script for SelectTopNRows command from SSMS  ******/

Create View [dbo].[vw_salesreason]
AS
SELECT [SalesReasonID]
      ,cast([Name] as varchar(50)) AS SalesReason
      ,[ReasonType]
      ,[ModifiedDate]
  FROM [AdventureWorks2019].[Sales].[SalesReason]
GO


