# TI Auto Collection

 开源情报自动收集工具

## 项目简介 / Project Introduction

TI Auto Collection 是一个自动化收集开源威胁情报的工具，能够从多个公开来源获取最新的威胁指标(IOC)，并将其转换为标准化的CSV格式存储。

TI Auto Collection is an automated tool for collecting open-source threat intelligence. It fetches the latest Indicators of Compromise (IOCs) from multiple public sources and stores them in standardized CSV format.

## 数据更新状态

| 数据源 | 最后更新时间 | 状态 |
|--------|------------|------|
| https://dsi.ut-capitole.fr/blacklists/download/cryptojacking.tar.gz | 2025-08-02 07:22:24 | ✅ 成功 |
| https://threatfox.abuse.ch/export/json/recent/ | 2025-08-02 07:22:25 | ✅ 成功 |

































































































































## 数据统计信息

| 统计项 | 值 |
|--------|----|
| 总记录数 | 111754 |

### IOC类型统计

| 类型 | 数量 |
|------|------|
| domain | 49132 |
| ip:port | 26060 |
| sha256_hash | 24401 |
| url | 9351 |
| md5_hash | 1970 |
| sha1_hash | 840 |

### 数据源统计

| 数据源 | 数量 |
|--------|------|
| https://threatfox.abuse.ch/export/json/recent/ | 100239 |
| https://dsi.ut-capitole.fr/blacklists/download/cryptojacking.tar.gz | 11515 |
