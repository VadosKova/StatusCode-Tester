--CREATE DATABASE [StatusTester]

USE [StatusTester]
GO

CREATE TABLE [Users] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [Username] VARCHAR(50),
	[Email] VARCHAR(100),
    [Password] VARCHAR(50),
    [IsAdmin] BIT DEFAULT 0
)

CREATE TABLE [Tests] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [Title] VARCHAR(255),
    [Description] VARCHAR(600)
)

CREATE TABLE [Questions] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [TestID] INT NOT NULL,
    [QuestionText] VARCHAR(600),
    FOREIGN KEY (TestID) REFERENCES [Tests](ID)
)

CREATE TABLE [Answers] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [QuestionID] INT NOT NULL,
    [AnswerText] VARCHAR(600),
    [IsCorrect] BIT,
    FOREIGN KEY ([QuestionID]) REFERENCES [Questions]([ID])
)

CREATE TABLE [Results] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [UserId] INT NOT NULL,
    [TestId] INT NOT NULL,
    [Score] FLOAT NOT NULL,
    [DateTaken] DATETIME DEFAULT GETDATE(),
    FOREIGN KEY ([UserId]) REFERENCES [Users]([ID]),
    FOREIGN KEY ([TestId]) REFERENCES [Tests]([ID])
)

CREATE TABLE [AnswerLogs] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [ResultId] INT NOT NULL,
    [UserId] INT NOT NULL,
    [QuestionId] INT NOT NULL,
    [AnswerId] INT NOT NULL,
    [IsCorrect] BIT,
    FOREIGN KEY (ResultId) REFERENCES [Results](ID),
    FOREIGN KEY (UserId) REFERENCES [Users](ID),
    FOREIGN KEY (AnswerId) REFERENCES [Answers](ID),
    FOREIGN KEY (QuestionId) REFERENCES [Questions](ID)
)