# FinalThreatFeed

🚀 开源威胁情报自动化搜集工具

## 项目简介

FinalThreatFeed是一个功能强大的威胁情报自动化搜集工具，能够从多个公开的威胁情报源获取数据，并进行统一格式处理和存储。

### 主要特性

- 📊 支持多种格式的威胁情报源（CSV、文本、MISP等）
- ⚡ 异步并发采集，提高效率
- 🧹 自动去重和数据清洗
- 📈 定期更新威胁情报
- 🎯 可配置的威胁情报源
- 🔍 支持IOC类型识别和分类

## 使用方法

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行工具

```bash
python main.py
```

## 订阅列表

| 状态 | 名称 | 类型 | 描述 | URL |
|------|------|------|------|-----|
| 🟢 | abuse.ch-SSL | csv | Sharing blocklist data for malicious SSL certificates and JA3/JA3s fingerprints | https://sslbl.abuse.ch/blacklist/sslblacklist.csv |
| 🟢 | Alienvault-IP-Reputation | csv | Alienvault IP Reputation Database | https://reputation.alienvault.com/reputation.generic |
| 🔴 | Phishtank | csv | Phishtank online valid phishing | https://data.phishtank.com/data/online-valid.csv |
| ⚫ | Tor_Exit_Nodes | text | Official Tor Exit Nodes | https://check.torproject.org/torbulkexitlist |
| 🟢 | IPsum-l4 | text | IPsum (aggregation of all feeds) - level 4 - very low false positives | https://raw.githubusercontent.com/stamparm/ipsum/master/levels/4.txt |
| 🟢 | IPsum-l5 | text | IPsum (aggregation of all feeds) - level 5 -  ultra false positives  | https://raw.githubusercontent.com/stamparm/ipsum/master/levels/5.txt |
| 🟢 | CIRCL OSINT Feed | misp | - | https://www.circl.lu/doc/misp/feed-osint/ |
| 🟢 | abuse.ch | misp | Sharing indicators of compromise (IOCs) associated with malware | https://threatfox.abuse.ch/downloads/misp |
| 🟢 | abuse.ch-Bazaar | misp | Sharing newly observed malware samples | https://bazaar.abuse.ch/downloads/misp/ |
| 🟢 | abuse.ch-URLhasus | misp | Sharing malicious URLs being used for malware distribution | https://urlhaus.abuse.ch/downloads/misp |
| 🟢 | Botvrij.eu | misp | - | https://www.botvrij.eu/data/feed-osint |

### 状态说明

- 🟢: 订阅正常
- 🔴: 订阅异常
- ⚫: 订阅已禁用

**最后更新时间:** 2025-12-05 17:03:30

## 配置说明

### feeds.yaml配置

在`config/feeds.yaml`文件中配置威胁情报源：

```yaml
feeds:
  - name: Feed名称
    enabled: true
    url: Feed URL
    source_format: feed类型  # csv, text, misp
    description: Feed描述
    # 其他类型特定配置
```

## 输出

- `output/collections.csv`: 原始收集的数据
- `final_threat.csv`: 去重后的最终威胁情报库

## 许可证

MIT License
