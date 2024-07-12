USE [MarketDBNeo]
GO

/****** Object:  Table [dbo].[t_index_minute_price]    Script Date: 2024/5/18 20:44:12 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

SET ANSI_PADDING ON
GO

CREATE TABLE [dbo].[t_index_minute_price](
  [curr_min] [VARCHAR](10) NOT NULL,
	[index_code] [VARCHAR](20) NOT NULL,
	[last_closep] [NUMERIC](18, 4) NOT NULL,
	[openp] [NUMERIC](18, 4) NOT NULL,
	[highp] [NUMERIC](18, 4) NOT NULL,
	[lowp] [NUMERIC](18, 4) NOT NULL,
	[closep] [NUMERIC](18, 4) NOT NULL,
	[min_pct_change] [NUMERIC](18, 4) NOT NULL,
	[amount] [NUMERIC](18, 4) NOT NULL,
	[volume] [NUMERIC](18, 4) NOT NULL,
	[acc_amount] [NUMERIC](18, 4) NOT NULL,
	[acc_volume] [NUMERIC](18, 4) NOT NULL,
	[update_time] [DATETIME] NOT NULL
) ON [PRIMARY]

GO

SET ANSI_PADDING OFF
GO

ALTER TABLE [dbo].[t_index_minute_price] ADD  CONSTRAINT [DF_t_index_minute_price_update_time]  DEFAULT (GETDATE()) FOR [update_time]
GO

USE [MarketDBNeo]
GO

/****** Object:  Table [dbo].[t_index_minute_price_full]    Script Date: 2024/5/18 20:44:33 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

SET ANSI_PADDING ON
GO

CREATE TABLE [dbo].[t_index_minute_price_full](
	[id] [BIGINT] IDENTITY(1,1) NOT NULL,
	[trade_date] [VARCHAR](10) NOT NULL,
	[curr_min] [VARCHAR](10) NOT NULL,
	[index_code] [VARCHAR](20) NOT NULL,
	[last_closep] [NUMERIC](18, 4) NOT NULL,
	[openp] [NUMERIC](18, 4) NOT NULL,
	[highp] [NUMERIC](18, 4) NOT NULL,
	[lowp] [NUMERIC](18, 4) NOT NULL,
	[closep] [NUMERIC](18, 4) NOT NULL,
	[min_pct_change] [NUMERIC](18, 4) NOT NULL,
	[amount] [NUMERIC](18, 4) NOT NULL,
	[volume] [NUMERIC](18, 4) NOT NULL,
	[acc_amount] [NUMERIC](18, 4) NOT NULL,
	[acc_volume] [NUMERIC](18, 4) NOT NULL,
	[update_time] [DATETIME] NOT NULL,
 CONSTRAINT [PK_t_index_minute_price_full] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO

SET ANSI_PADDING OFF
GO

ALTER TABLE [dbo].[t_index_minute_price_full] ADD  CONSTRAINT [DF_t_index_minute_price_full_update_time]  DEFAULT (GETDATE()) FOR [update_time]
GO


USE [MarketDBNeo]
GO

/****** Object:  Table [dbo].[t_indexfuture_minute_price]    Script Date: 2024/5/18 20:44:55 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

SET ANSI_PADDING ON
GO

CREATE TABLE [dbo].[t_indexfuture_minute_price](
	[id] [BIGINT] IDENTITY(1,1) NOT NULL,
  [curr_min] [VARCHAR](10) NOT NULL,
	[indexfuture_code] [VARCHAR](20) NOT NULL,
	[last_closep] [NUMERIC](18, 4) NOT NULL,
	[last_settlep] [NUMERIC](18, 4) NOT NULL,
	[openp] [NUMERIC](18, 4) NOT NULL,
	[highp] [NUMERIC](18, 4) NOT NULL,
	[lowp] [NUMERIC](18, 4) NOT NULL,
	[closep] [NUMERIC](18, 4) NOT NULL,
	[min_pct_change] [NUMERIC](18, 4) NOT NULL,
	[amount] [NUMERIC](18, 4) NOT NULL,
	[volume] [NUMERIC](18, 4) NOT NULL,
	[acc_amount] [NUMERIC](18, 4) NOT NULL,
	[acc_volume] [NUMERIC](18, 4) NOT NULL,
	[holding] [NUMERIC](18, 4) NOT NULL,
	[update_time] [DATETIME] NOT NULL
) ON [PRIMARY]

GO

SET ANSI_PADDING OFF
GO

ALTER TABLE [dbo].[t_indexfuture_minute_price] ADD  CONSTRAINT [DF_t_indexfuture_minute_price_update_time]  DEFAULT (GETDATE()) FOR [update_time]
GO




USE [MarketDBNeo]
GO

/****** Object:  Table [dbo].[t_indexfuture_minute_price_full]    Script Date: 2024/5/18 20:45:08 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

SET ANSI_PADDING ON
GO

CREATE TABLE [dbo].[t_indexfuture_minute_price_full](
	[id] [BIGINT] IDENTITY(1,1) NOT NULL,
	[trade_date] [VARCHAR](10) NOT NULL,
	[curr_min] [VARCHAR](10) NOT NULL,
	[indexfuture_code] [VARCHAR](20) NOT NULL,
	[last_closep] [NUMERIC](18, 4) NOT NULL,
	[last_settlep] [NUMERIC](18, 4) NOT NULL,
	[openp] [NUMERIC](18, 4) NOT NULL,
	[highp] [NUMERIC](18, 4) NOT NULL,
	[lowp] [NUMERIC](18, 4) NOT NULL,
	[closep] [NUMERIC](18, 4) NOT NULL,
	[min_pct_change] [NUMERIC](18, 4) NOT NULL,
	[amount] [NUMERIC](18, 4) NOT NULL,
	[volume] [NUMERIC](18, 4) NOT NULL,
	[acc_amount] [NUMERIC](18, 4) NOT NULL,
	[acc_volume] [NUMERIC](18, 4) NOT NULL,
	[holding] [NUMERIC](18, 4) NOT NULL,
	[update_time] [DATETIME] NOT NULL,
 CONSTRAINT [PK_t_indexfuture_minute_price_full] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO

SET ANSI_PADDING OFF
GO

ALTER TABLE [dbo].[t_indexfuture_minute_price_full] ADD  CONSTRAINT [DF_t_indexfuture_minute_price_full_update_time]  DEFAULT (GETDATE()) FOR [update_time]
GO

