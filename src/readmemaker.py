#!/usr/bin/env python3
"""
README生成器
根据feeds.yaml和实际拉取状态生成README.md文件，包含订阅列表和存活状态标识
"""

import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('README_Maker')

class READMEGenerator:
    def __init__(self, feeds_config_path: str, readme_path: str = 'README.md'):
        """
        初始化README生成器
        
        Args:
            feeds_config_path: feeds.yaml配置文件路径
            readme_path: 生成的README.md文件路径
        """
        self.feeds_config_path = feeds_config_path
        self.readme_path = readme_path
        self.feeds_data = []
        self.feed_status = {}
    
    def load_feeds_config(self):
        """加载feeds.yaml配置文件"""
        try:
            with open(self.feeds_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self.feeds_data = config.get('feeds', [])
            logger.info(f"Loaded {len(self.feeds_data)} feeds from {self.feeds_config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load feeds config: {e}")
            return False
    
    def set_feed_status(self, feed_status: Dict[str, str]):
        """
        设置feed状态，由core.py传递实际拉取结果
        
        Args:
            feed_status: 字典格式，键为feed名称，值为状态('alive', 'error', 'disabled')
        """
        self.feed_status = feed_status
        logger.info(f"Set status for {len(feed_status)} feeds")
    
    def generate_readme(self):
        """生成README.md文件"""
        logger.info("Generating README.md...")
        
        # 构建README内容
        content = []
        
        # 项目标题
        content.append("# FinalThreatFeed")
        content.append("")
        content.append("🚀 **高性能开源威胁情报聚合引擎**")
        content.append("")
        
        # 项目简介
        content.append("## 📖 项目简介")
        content.append("")
        content.append("FinalThreatFeed 是一款现代化的威胁情报（CTI）自动化采集与融合框架。它基于高性能异步架构设计，旨在解决多源情报采集难、格式混乱、数据冗余等痛点。")
        content.append("")
        content.append("通过标准化的数据处理管道，FinalThreatFeed 能够从全球开源情报源中持续汲取高价值数据，自动完成清洗、去重与结构化处理，为企业的安全防御体系提供精准、鲜活的威胁情报支撑。")
        content.append("")
        
        # 核心特性
        content.append("### ✨ 核心特性")
        content.append("")
        content.append("- ⚡ **极速异步架构**: 采用 Python Asyncio + HTTPX 构建高并发采集核心，大幅提升数据吞吐效率。")
        content.append("- 🧩 **全栈格式兼容**: 原生支持 MISP、CSV、Text 等主流情报格式，轻松打破数据源格式壁垒。")
        content.append("- 🧹 **智能清洗去重**: 内置精细化数据治理算法，自动剔除噪声与重复数据，确保情报的高信噪比。")
        content.append("- 🔄 **全生命周期管理**: 自动化的情报老化与更新机制，确保本地情报库始终保持最新状态。")
        content.append("- 🛠️ **灵活扩展配置**: 基于 YAML 的声明式配置管理，无需编码即可快速接入新的情报源。")
        content.append("- 🏷️ **深度 IOC 识别**: 自动解析并分类 IP、Domain、URL 等关键威胁指标，赋能精细化分析。")
        content.append("")
        # 更新时间
        content.append(f"> 🕒 **最后更新时间:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
        content.append("")

        
        # 订阅列表
        content.append("## 📡 订阅源状态监控")
        content.append("")
        # 移除描述列，保持表格简洁大气
        content.append("| 运行状态 | 情报源名称 | 格式类型 | 源地址 (URL) |")
        content.append("|:---:|---|:---:|---|")
        
        # 添加订阅行
        for feed in self.feeds_data:
            # 状态标识
            status = self.feed_status.get(feed['name'], 'disabled')
            if status == 'alive':
                status_emoji = '🟢'
            elif status == 'error':
                status_emoji = '🔴'
            else:
                status_emoji = '⚫'
            
            # 订阅信息
            name = feed['name']
            feed_type = feed['source_format']
            url = feed.get('url', '-')
            
            # 添加行
            content.append(f"| {status_emoji} | **{name}** | `{feed_type}` | {url} |")
        
        content.append("")
        
        # 状态说明
        content.append("#### 📊 运行状态图例")
        content.append("- 🟢 **运行正常**: 成功连接并获取最新情报数据")
        content.append("- 🔴 **采集异常**: 连接超时或源数据格式错误")
        content.append("- ⚫ **已禁用**: 当前配置下未启用的情报源")
        content.append("")
        
        # 使用说明
        content.append("## 🚀 快速开始")
        content.append("")
        content.append("### 1. 环境准备")
        content.append("```bash")
        content.append("pip install -r requirements.txt")
        content.append("```")
        content.append("")
        content.append("### 2. 启动引擎")
        content.append("```bash")
        content.append("python main.py")
        content.append("```")
        content.append("")
        
        # 配置说明
        content.append("## ⚙️ 配置指南")
        content.append("")
        content.append("所有情报源均通过 `config/feeds.yaml` 进行声明式管理，支持灵活的自定义扩展：")
        content.append("")
        content.append("```yaml")
        content.append("feeds:")
        # 使用单引号包裹，防止双引号转义问题
        content.append('  - name: "Feed名称"')
        content.append('    enabled: true')
        content.append('    url: "[https://example.com/feed.csv](https://example.com/feed.csv)"')
        content.append('    source_format: "csv"  # 支持 csv, text, misp')
        content.append('    description: "简短的情报源描述"')
        content.append("    # 不同类型的源支持特定的高级配置参数")
        content.append("```")
        content.append("")
        
        # 输出路径
        content.append("## 📂 数据产出")
        content.append("")
        content.append("- `output/description.json`: **情报源下载描述**")
        content.append("- `output/collections.csv`: **原始采集数据** (增量缓存)")
        content.append("- `output/final_threat.csv`: **最终情报库** (已清洗、去重、标准化的全量高价值情报)")
        content.append("")
        
        # 许可证
        content.append("## 📄 开源协议")
        content.append("")
        content.append("本项目遵循 [MIT License](LICENSE) 开源协议。")
        content.append("")
        
        # 写入文件
        try:
            with open(self.readme_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            logger.info(f"README.md generated at {self.readme_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write README.md: {e}")
            return False
    
    def run(self):
        """执行完整的生成流程"""
        if not self.load_feeds_config():
            return False
        
        # 确保feed_status不为空，如果为空（例如手动运行脚本时），填充默认状态
        if not self.feed_status:
            logger.warning("No feed status provided. Using default status.")
        
        # 补全状态
        for feed in self.feeds_data:
            if feed['name'] not in self.feed_status:
                if feed.get('enabled', False):
                    self.feed_status[feed['name']] = 'unknown'
                else:
                    self.feed_status[feed['name']] = 'disabled'
        
        return self.generate_readme()

if __name__ == "__main__":
    # 配置路径
    feeds_config = Path("config/feeds.yaml")
    readme_path = Path("README.md")
    
    # 创建生成器并运行
    generator = READMEGenerator(str(feeds_config), str(readme_path))
    if generator.run():
        logger.info("README generation completed successfully!")
    else:
        logger.error("README generation failed!")