USE [AdventureWorks2019]
GO

/****** Object:  View [dbo].[vw_person]    Script Date: 6/3/2023 10:48:08 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

/****** Script for SelectTopNRows command from SSMS  ******/


Create View [dbo].[vw_person]
AS

SELECT [BusinessEntityID]
      ,[PersonType]
      ,[NameStyle]
      ,[Title]
      ,cast([FirstName] as varchar(50)) AS FirstName
      ,cast([MiddleName] as varchar(50)) AS MiddleName
      ,cast([LastName] as varchar(50)) AS LastName
      ,[Suffix]
      ,[EmailPromotion]
      ,[AdditionalContactInfo]
      ,[Demographics]
      ,[rowguid]
      ,[ModifiedDate]
  FROM [AdventureWorks2019].[Person].[Person]
GO


