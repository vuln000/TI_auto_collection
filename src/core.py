import yaml
import logging
import asyncio
import sys
from pathlib import Path
from typing import Dict, List
from .fetchers import FeedFetcher
from .writer import FeedWriter
from .collector import DataCollector
# 导入README生成器
from .readmemaker import READMEGenerator

# 配置日志格式，方便在 GitHub Actions Console 中查看
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    datefmt='%H:%M:%S'
)
# 抑制 httpx 的 INFO 级别的调试输出
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger("Core")

class CoreEngine:
    def __init__(self, feed_path: str = "config/feeds.yaml", setting_path: str = "config/setting.yaml"):
        """
        初始化核心引擎
        :param feed_path: 订阅配置文件路径
        :param setting_path: 系统设置文件路径
        """
        self.project_root = Path(__file__).parent.parent
        self.setting_file = self.project_root / setting_path
        self.feed_file = self.project_root / feed_path
        self.config_setting = {}
        self.config_feeds = {}
        
        # 运行时状态统计
        self.stats = {
            "total_feeds": 0,
            "enabled_feeds": 0,
            "success": 0,
            "failed": 0
        }
        
        # 跟踪每个feed的实际拉取状态
        self.feed_status = {}

    def load_config(self):
        """
        第一步：读取并验证 YAML 配置文件
        同时加载系统设置文件
        """
        # 1. 加载系统设置文件
        logger.info(f"Loading settings from: {self.setting_file}")
        try:
            with open(self.setting_file, 'r', encoding='utf-8') as f:
                self.config_setting = yaml.safe_load(f)
        except Exception as e:
            logger.critical(f"Failed to load settings from {self.setting_file}: {e}")
            sys.exit(1)
            
        # 2. 加载 feeds 配置文件
        logger.info(f"Loading configuration from: {self.feed_file}")
        try:
            with open(self.feed_file, 'r', encoding='utf-8') as f:
                self.config_feeds = yaml.safe_load(f)
        except Exception as e:
            logger.critical(f"Failed to load config from {self.feed_file}: {e}")
            sys.exit(1)
                
    def get_active_feeds(self) -> List[Dict]:
        """
        第二步：筛选出需要运行的 Feed (enabled: true)
        """
        all_feeds = self.config_feeds.get("feeds", [])
        self.stats["total_feeds"] = len(all_feeds)
        
        # 过滤 active feeds
        active_feeds = [
            f for f in all_feeds 
            if f.get("enabled", False) is True
        ]
        
        self.stats["enabled_feeds"] = len(active_feeds)
        logger.info(f"Found {len(active_feeds)} active feeds out of {len(all_feeds)} total.")
        return active_feeds

    async def run_pipeline(self):
        """
        第三步：流水线调度器
        """
        # 1. 加载全局配置
        self.load_config()
        
        # 2. 获取活跃的任务
        active_feeds = self.get_active_feeds()
        if not active_feeds:
            logger.warning("No active feeds to process.")
            return

        # 3. 初始化 Writer
        writer = FeedWriter(output_dir="output")
        await writer.start()  # 启动消费者后台任务

        try:
            # 4. 初始化数据获取器，传入 fetcher 配置和 writer
            tasks = []
            task_feed_map = {}
            fetcher = FeedFetcher(self.config_setting.get('fetcher', {}), writer=writer)
            
            # 使用上下文管理器来确保HTTP客户端正确关闭
            async with fetcher:
                for feed_cfg in active_feeds:
                    # 启动所有 Feed 的下载任务
                    task = asyncio.create_task(fetcher.fetch_feed(feed_cfg))
                    tasks.append(task)
                    task_feed_map[task] = feed_cfg
                    
                # 等待所有 Fetcher 任务处理完成，捕获每个任务的结果
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 更新每个feed的状态
            self.stats["success"] = 0
            self.stats["failed"] = 0
            
            for result, task in zip(results, tasks):
                feed_cfg = task_feed_map[task]
                feed_name = feed_cfg['name']
                
                if isinstance(result, Exception):
                    # 任务失败
                    self.feed_status[feed_name] = 'error'
                    self.stats["failed"] += 1
                    logger.error(f"[{feed_name}] Pull failed: {result}")
                else:
                    # 任务成功
                    self.feed_status[feed_name] = 'alive'
                    self.stats["success"] += 1
                    logger.info(f"[{feed_name}] Pull succeeded")
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            self.stats["failed"] += 1
        finally:
            # 5. 确保 Writer 处理完队列中的剩余数据并安全关闭
            await writer.stop()
            self._print_summary()
            collector = DataCollector(keep_days=self.config_setting.get('collector', {}).get('keep_days', 60))
            collector.process()
            
            # 6. 生成 README 文件，包含实际拉取状态
            logger.info("Generating README with feed status...")
            try:
                # 为未处理的feed设置状态
                for feed in self.config_feeds.get("feeds", []):
                    feed_name = feed['name']
                    if feed_name not in self.feed_status:
                        if feed.get('enabled', False):
                            self.feed_status[feed_name] = 'disabled'  # 未处理的启用feed
                        else:
                            self.feed_status[feed_name] = 'disabled'
                
                # 创建README生成器
                readme_generator = READMEGenerator(
                    feeds_config_path=str(self.feed_file),
                    readme_path=str(self.project_root / "README.md")
                )
                
                # 设置feed状态
                readme_generator.set_feed_status(self.feed_status)
                
                # 生成README
                if readme_generator.run():
                    logger.info("README generated successfully!")
                else:
                    logger.error("Failed to generate README")
            except Exception as e:
                logger.error(f"Error generating README: {e}")
    def _print_summary(self):
        print("\n" + "="*30)
        print(f" PIPELINE SUMMARY")
        print(f" Total:   {self.stats['total_feeds']}")
        print(f" Success: {self.stats['success']}")
        print(f" Failed:  {self.stats['failed']}")
        print("="*30 + "\n")

# ==========================================
# 入口测试 (Entry Point)
# ==========================================
if __name__ == "__main__":
    # 模拟运行
    engine = CoreEngine()
    try:
        asyncio.run(engine.run_pipeline())
    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user.")