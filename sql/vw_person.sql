USE [AdventureWorks2019]
GO

/****** Object:  View [dbo].[vw_person]    Script Date: 7/25/2023 4:13:05 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


/****** Script for SelectTopNRows command from SSMS  ******/


ALTER View [dbo].[vw_person]
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
      ,[rowguid]
      ,[ModifiedDate]
	  ,	cast(CONVERT(datetime, LEFT(Survey.ref.value(N'declare default element namespace "http://schemas.microsoft.com/sqlserver/2004/07/adventure-works/IndividualSurvey";BirthDate','varchar(20)'), 10)) as varchar(20)) AS [BirthDate],
	cast(Survey.ref.value(N'declare default element namespace "http://schemas.microsoft.com/sqlserver/2004/07/adventure-works/IndividualSurvey";MaritalStatus','varchar(1)') as varchar(1)) AS [MaritalStatus], 	
    cast(Survey.ref.value(N'declare default element namespace "http://schemas.microsoft.com/sqlserver/2004/07/adventure-works/IndividualSurvey";Gender','varchar(1)') AS varchar(1)) AS [Gender], 
    cast(Survey.ref.value(N'declare default element namespace "http://schemas.microsoft.com/sqlserver/2004/07/adventure-works/IndividualSurvey";TotalChildren','int') AS int) AS [TotalChildren], 
    cast(Survey.ref.value(N'declare default element namespace "http://schemas.microsoft.com/sqlserver/2004/07/adventure-works/IndividualSurvey";NumberChildrenAtHome','int') AS int)  AS [NumberChildrenAtHome], 
    CAST(Survey.ref.value(N'declare default element namespace "http://schemas.microsoft.com/sqlserver/2004/07/adventure-works/IndividualSurvey";HomeOwnerFlag','int') AS varchar(1)) AS [HouseOwnerFlag], 
    cast(Survey.ref.value(N'declare default element namespace "http://schemas.microsoft.com/sqlserver/2004/07/adventure-works/IndividualSurvey";NumberCarsOwned','int') AS INT) AS [NumberCarsOwned], 
	CONVERT(datetime, LEFT(Survey.ref.value(N'declare default element namespace "http://schemas.microsoft.com/sqlserver/2004/07/adventure-works/IndividualSurvey";DateFirstPurchase','varchar(20)'), 10)) AS [DateFirstPurchase],     
    cast(Survey.ref.value(N'declare default element namespace "http://schemas.microsoft.com/sqlserver/2004/07/adventure-works/IndividualSurvey";CommuteDistance','varchar(15)') AS varchar(15)) AS [CommuteDistance],
	cast(Person.Demographics.value(N'declare default element namespace "http://schemas.microsoft.com/sqlserver/2004/07/adventure-works/IndividualSurvey";(IndividualSurvey/Education)[1]','varchar(40)') AS varchar(40)) as [Education],
	cast(Person.Demographics.value(N'declare default element namespace "http://schemas.microsoft.com/sqlserver/2004/07/adventure-works/IndividualSurvey";(IndividualSurvey/Occupation)[1]','varchar(40)') AS varchar(40)) as [Occupation]
  FROM [AdventureWorks2019].[Person].[Person]
  cross apply Person.[Demographics].nodes(N'declare default element namespace "http://schemas.microsoft.com/sqlserver/2004/07/adventure-works/IndividualSurvey";IndividualSurvey') AS Survey(ref) 
GO


