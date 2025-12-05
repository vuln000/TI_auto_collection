import pandas as pd
import os
import logging
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
)
logger = logging.getLogger("Collector")

class DataCollector:
    """
    数据收集与清洗器
    职责：
    1. 读取 collections.csv (增量) 和 final_threat.csv (全量)
    2. 合并并去重
    3. 全局清洗：剔除所有超过 60 天的数据（无论是新来的还是库里老的）
    4. 覆写 final_threat.csv
    5. 删除 collections.csv
    """
    def __init__(self, input_path="output/collections.csv", output_path="output/final_threat.csv",keep_days = 60):
        self.input_path = input_path
        self.output_path = output_path
        self.keep_days = keep_days
    def process(self):
        df_new = pd.DataFrame()
        df_existing = pd.DataFrame()

        # 1. 读取新采集的数据 (collections.csv)
        if os.path.exists(self.input_path):
            try:
                df_new = pd.read_csv(self.input_path, dtype=str)
                if not df_new.empty:
                    logger.info(f"Read {len(df_new)} new rows from {self.input_path}")
                    # 预处理新数据的时间戳：Unix -> YYYY-MM-DD
                    # 统一成字符串格式，方便后续合并
                    df_new['timestamp'] = pd.to_datetime(
                        df_new['timestamp'].astype(float), unit='s'
                    ).dt.strftime('%Y-%m-%d')
            except Exception as e:
                logger.error(f"Error reading new data: {e}")
        else:
            logger.info(f"No new input file found: {self.input_path}")

        # 2. 读取已有的最终情报库 (final_threat.csv)
        if os.path.exists(self.output_path):
            try:
                df_existing = pd.read_csv(self.output_path, dtype=str)
                logger.info(f"Loaded {len(df_existing)} existing records from {self.output_path}")
            except Exception as e:
                logger.error(f"Error reading existing database: {e}")

        # 如果两边都没数据，直接结束
        if df_new.empty and df_existing.empty:
            logger.info("No data to process.")
            self._remove_source_file()
            return

        try:
            # 3. 合并数据
            # 使用 concat 合并，ignore_index=True 重置索引
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            
            # 4. 全局去重
            # keep='last' 确保如果新老数据 IOC 冲突，保留新采集的那条（因为时间更新）
            if 'value' in df_combined.columns:
                before_dedup = len(df_combined)
                df_combined.drop_duplicates(subset=['value'], keep='last', inplace=True)
                logger.info(f"Deduplication: {before_dedup} -> {len(df_combined)} records")

            # 5. 全局时间过滤（逻辑修正：在所有操作完成后执行）
            # 将 timestamp 列转为 datetime 对象进行比较
            # errors='coerce' 会将无法解析的日期变为 NaT，稍后可以过滤掉
            combined_dates = pd.to_datetime(df_combined['timestamp'], errors='coerce')
            
            # 计算 60 天前的日期
            cutoff_date = datetime.now() - timedelta(days=self.keep_days)
            
            # 筛选：保留 (日期有效) 且 (日期 >= 截止日期) 的记录
            valid_mask = (combined_dates.notna()) & (combined_dates >= cutoff_date)
            
            df_final = df_combined[valid_mask]
            
            removed_count = len(df_combined) - len(df_final)
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} expired records (older than 60 days).")

            # 6. 写入文件 (全量覆写)
            if not df_final.empty:
                df_final.to_csv(self.output_path, index=False, encoding='utf-8')
                logger.info(f"Successfully saved {len(df_final)} valid records to {self.output_path}")
            else:
                # 如果过滤完没数据了（比如全过期了），且原文件存在，是否要清空？
                # 这里选择创建一个空文件保留表头
                df_final.to_csv(self.output_path, index=False, encoding='utf-8')
                logger.info(f"Database is empty after cleanup. Saved empty file to {self.output_path}")

            # 7. 删除源文件
            self._remove_source_file()

        except Exception as e:
            logger.error(f"Collector process failed: {e}")
            # 出错时不删除源文件，以便排查

    def _remove_source_file(self):
        """辅助方法：删除源输入文件"""
        if os.path.exists(self.input_path):
            try:
                os.remove(self.input_path)
                logger.info(f"Deleted source file: {self.input_path}")
            except Exception as e:
                logger.error(f"Failed to delete source file {self.input_path}: {e}")

if __name__ == "__main__":
    # 路径自适应
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 判断脚本位置
    if current_dir.endswith("src"):
        project_root = os.path.dirname(current_dir)
        input_csv = os.path.join(project_root, "output", "collections.csv")
        output_csv = os.path.join(project_root, "final_threat.csv")
    else:
        # 假设在根目录
        input_csv = "output/collections.csv"
        output_csv = "/output/final_threat.csv"
        
    collector = DataCollector(input_path=input_csv, output_path=output_csv)
    collector.process()