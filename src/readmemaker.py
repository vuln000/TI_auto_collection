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
        content.append("🚀 开源威胁情报自动化搜集工具")
        content.append("")
        
        # 项目简介
        content.append("## 项目简介")
        content.append("")
        content.append("FinalThreatFeed是一个功能强大的威胁情报自动化搜集工具，能够从多个公开的威胁情报源获取数据，并进行统一格式处理和存储。")
        content.append("")
        content.append("### 主要特性")
        content.append("")
        content.append("- 📊 支持多种格式的威胁情报源（CSV、文本、MISP等）")
        content.append("- ⚡ 异步并发采集，提高效率")
        content.append("- 🧹 自动去重和数据清洗")
        content.append("- 📈 每日自动更新威胁情报")
        content.append("- 🎯 可配置的威胁情报源")
        content.append("- 🔍 支持IOC类型识别和分类")
        content.append("")
        
        # 订阅列表
        content.append("## 订阅列表")
        content.append("")
        content.append("| 状态 | 名称 | 类型 | 描述 | URL |")
        content.append("|------|------|------|------|-----|")
        
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
            description = feed.get('description', '-')
            url = feed.get('url', '-')
            
            # 添加行
            content.append(f"| {status_emoji} | {name} | {feed_type} | {description} | {url} |")
        
        content.append("")
        
        # 状态说明
        content.append("### 状态说明")
        content.append("")
        content.append("- 🟢: 订阅正常")
        content.append("- 🔴: 订阅异常")
        content.append("- ⚫: 订阅已禁用")
        content.append("")
        
        # 更新时间
        content.append(f"**最后更新时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("")
        
        # 配置说明
        content.append("## 配置说明")
        content.append("")
        content.append("### feeds.yaml配置")
        content.append("")
        content.append("在`config/feeds.yaml`文件中配置威胁情报源：")
        content.append("")
        content.append("```yaml")
        content.append("feeds:")
        content.append("  - name: ""Feed名称""")
        content.append("    enabled: true")
        content.append("    url: ""Feed URL""")
        content.append("    source_format: ""feed类型""  # csv, text, misp")
        content.append("    description: ""Feed描述""")
        content.append("    # 其他类型特定配置")
        content.append("```")
        content.append("")
        
        # 输出路径
        content.append("## 输出")
        content.append("")
        content.append("- `output/collections.csv`: 原始收集的数据")
        content.append("- `final_threat.csv`: 去重后的最终威胁情报库")
        content.append("")
        
        # 许可证
        content.append("## 许可证")
        content.append("")
        content.append("MIT License")
        content.append("")
        
        # 写入文件
        with open(self.readme_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        logger.info(f"README.md generated at {self.readme_path}")
        return True
    
    def run(self):
        """执行完整的生成流程"""
        if not self.load_feeds_config():
            return False
        
        # 确保feed_status不为空
        if not self.feed_status:
            logger.warning("No feed status provided. Using default status.")
            # 为未设置状态的feed设置默认值
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
