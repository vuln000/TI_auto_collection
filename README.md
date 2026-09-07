# FinalThreatFeed

🚀 **High-Performance Open Source Threat Intelligence Aggregation Engine**

## 📖 Project Introduction

FinalThreatFeed is a modern threat intelligence (CTI) automated collection and fusion framework. It is designed based on high-performance asynchronous architecture to solve pain points such as difficulty in multi-source intelligence collection, format confusion, and data redundancy.

Through a standardized data processing pipeline, FinalThreatFeed continuously extracts high-value data from global open-source intelligence sources, automatically completes cleaning, deduplication, and structuring processes, providing accurate and fresh threat intelligence support for enterprise security defense systems.

### ✨ Core Features

- ⚡ **High-Speed Asynchronous Architecture**: Built with Python Asyncio + HTTPX for high concurrency collection core, significantly improving data throughput efficiency.
- 🧩 **Full-Stack Format Compatibility**: Native support for mainstream intelligence formats such as MISP, CSV, Text, and RSS, easily breaking down data source format barriers.
- 🧹 **Intelligent Cleaning and Deduplication**: Built-in refined data governance algorithms automatically eliminate noise and duplicate data, ensuring high signal-to-noise ratio of intelligence.
- 🔄 **Full Lifecycle Management**: Automated intelligence aging and update mechanisms ensure the local intelligence library always stays up-to-date.
- 🛠️ **Flexible Extension Configuration**: YAML-based declarative configuration management, allowing quick access to new intelligence sources without coding.
- 🏷️ **Deep IOC Identification**: Automatically parse and classify key threat indicators such as IP, Domain, URL, enabling refined analysis.
- 🤖 **LLM-Powered Unstructured Data Processing**: Leverages Google Gemini API to extract IOCs from unstructured data sources like RSS feeds, enhancing intelligence coverage.

> 🕒 **Last Update Time:** `2026-09-07 22:38:32`

## 📡 Feed Status Monitoring

| Status | Feed Name | Format Type | Source Address (URL) |
|:---:|---|:---:|---|
| 🟢 | **abuse.ch-SSL** | `csv` | https://sslbl.abuse.ch/blacklist/sslblacklist.csv |
| 🟢 | **Alienvault-IP-Reputation** | `csv` | https://reputation.alienvault.com/reputation.generic |
| 🔴 | **Phishtank** | `csv` | https://data.phishtank.com/data/online-valid.csv |
| 🟢 | **mining-pool-block-list** | `csv` | https://raw.githubusercontent.com/vuln000/mining-pool-block-list/refs/heads/main/mining_pools.csv |
| ⚫ | **Tor_Exit_Nodes** | `text` | https://check.torproject.org/torbulkexitlist |
| 🟢 | **IPsum-l4** | `text` | https://raw.githubusercontent.com/stamparm/ipsum/master/levels/4.txt |
| 🟢 | **IPsum-l5** | `text` | https://raw.githubusercontent.com/stamparm/ipsum/master/levels/5.txt |
| 🟢 | **CIRCL OSINT Feed** | `misp` | https://www.circl.lu/doc/misp/feed-osint/ |
| 🟢 | **abuse.ch** | `misp` | https://threatfox.abuse.ch/downloads/misp |
| 🟢 | **abuse.ch-Bazaar** | `misp` | https://bazaar.abuse.ch/downloads/misp/ |
| 🟢 | **abuse.ch-URLhasus** | `misp` | https://urlhaus.abuse.ch/downloads/misp |
| 🟢 | **Botvrij.eu** | `misp` | https://www.botvrij.eu/data/feed-osint |
| 🟢 | **SecurityVedors** | `rss` | https://raw.githubusercontent.com/EndlessFractal/Threat-Intel-Feed/main/feed.xml |

#### 📊 Status Legend
- 🟢 **Running Normally**: Successfully connected and obtained latest intelligence data
- 🔴 **Collection Error**: Connection timeout or source data format error
- ⚫ **Disabled**: Intelligence source not enabled in current configuration

## 🤖 LLM-Powered Intelligence Processing

FinalThreatFeed integrates cutting-edge Large Language Model (LLM) technology to process unstructured threat intelligence data, particularly from RSS sources. Here's how it works:

1. **Intelligent Content Extraction**: Uses Google Gemini API to analyze web content from RSS feeds and automatically extract IOCs (Indicators of Compromise).
2. **Advanced Data Cleaning**: Automatically removes evasion symbols like [.] or [at] and normalizes data to lowercase.
3. **Structured Output**: Converts unstructured text into standardized JSON format for seamless integration with the intelligence pipeline.
4. **Enhanced Coverage**: Expands intelligence sources beyond traditional structured formats to include rich unstructured data from security blogs, threat reports, and news sources.

## 🚀 Quick Start

### 1. Environment Setup
```bash
pip install -r requirements.txt
```

### 2. Start the Engine
```bash
python main.py
```

## ⚙️ Configuration Guide

All intelligence sources are managed declaratively through `config/feeds.yaml`, supporting flexible custom extensions:

```yaml
feeds:
  - name: "Feed Name"
    enabled: true
    url: "https://example.com/feed.csv"
    source_format: "csv"  # Supports csv, text, misp, rss
    description: "Brief feed description"
    # Different types of sources support specific advanced configuration parameters
```

## 📂 Data Output

- `output/description.json`: **Intelligence Source Download Description**
- `output/collections.csv`: **Raw Collection Data** (incremental cache)
- `output/final_threat.csv`: **Final Intelligence Database** (cleaned, deduplicated, standardized high-value intelligence)

## 📄 Open Source License

This project follows the [MIT License](LICENSE) open source agreement.
