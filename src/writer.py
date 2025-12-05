import asyncio
import csv
import os
import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger("FeedWriter")

class FeedWriter:
    """
    独立的数据写入器，使用生产者-消费者模式。
    支持异步接收数据，串行写入文件，避免I/O阻塞和文件冲突。
    统一使用 MISP 格式的字段进行写入。
    """
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.queue = asyncio.Queue()
        self.is_running = False
        self._writer_task = None
        
        # 定义MISP聚合CSV的保存路径
        os.makedirs(self.output_dir, exist_ok=True)
        self.collections_path = os.path.join(self.output_dir, "collections.csv")
        
        # 初始化文件头部（如果文件不存在）
        self._init_files()

    def _init_files(self):
        """初始化CSV文件头"""
        if not os.path.exists(self.collections_path):
            with open(self.collections_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'feed_name',
                     'type', 'value', 'comment'
                ])

    async def start(self):
        """启动后台写入消费者任务"""
        self.is_running = True
        self._writer_task = asyncio.create_task(self._consume_loop())
        logger.info("FeedWriter consumer task started.")

    async def stop(self):
        """优雅停止写入任务"""
        logger.info("Stopping FeedWriter, waiting for queue to empty...")
        # 等待队列中的所有任务被处理完
        await self.queue.join()
        self.is_running = False
        # 发送停止信号
        await self.queue.put(None)
        if self._writer_task:
            await self._writer_task
        logger.info("FeedWriter stopped.")


    async def enqueue_generic(self, feed_name: str, attribute: Dict):
        """
        通用入队接口。
        注意：调用此接口前，data 必须已经是符合 collections.csv 字段结构的字典。
        :param data: 符合 MISP CSV 结构的字典
        """
        
        data = {
            'timestamp': attribute.get('timestamp', datetime.now().timestamp()),
            'feed_name': feed_name,
            'type': attribute.get('type', ''),
            'value': attribute.get('value', ''),
            'comment': attribute.get('comment', '')
        }
        await self.queue.put({'content': data})
    async def _consume_loop(self):
        """
        消费者循环：批量获取数据并统一写入文件
        策略：每积攒 BATCH_SIZE 条，或者每过 FLUSH_INTERVAL 秒，执行一次写入
        """
        BATCH_SIZE = 1000       # 批量大小
        FLUSH_INTERVAL = 2.0    # 超时刷新时间（秒）
        
        buffer = []
        
        while True:
            try:
                # 1. 尝试获取数据，设置超时时间
                # 如果超过 FLUSH_INTERVAL 秒没拿到数据，会抛出 asyncio.TimeoutError
                item = await asyncio.wait_for(self.queue.get(), timeout=FLUSH_INTERVAL)
            
            except asyncio.TimeoutError:
                # 2. 超时处理：如果缓冲区有数据，强制写入
                if buffer:
                    self._write_batch(buffer)
                    buffer = [] # 清空缓冲区
                continue

            # 3. 停止信号处理
            if item is None:
                # 退出前把剩下的数据写完
                if buffer:
                    self._write_batch(buffer)
                self.queue.task_done()
                break

            try:
                # 4. 正常数据处理
                content = item.get('content')
                if content:
                    buffer.append(content)
                
                # 5. 容量处理：如果积攒够了，写入
                if len(buffer) >= BATCH_SIZE:
                    self._write_batch(buffer)
                    buffer = []

            except Exception as e:
                logger.error(f"Error processing record: {e}")
            finally:
                # 标记该任务完成（注意：为了防止 stop() 中的 join() 死锁，取出即标记）
                self.queue.task_done()

    def _write_batch(self, rows: list[Dict]):
        """
        实际执行批量写入 CSV 动作
        替代原有的 _write_row，使用 writerows 提高效率
        """
        if not rows:
            return

        # 注意：这里是同步IO，但在独立Task中运行，不会阻塞网络请求
        try:
            with open(self.collections_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'timestamp', 'feed_name',
                    'type', 'value', 'comment'
                ])
                # 核心优化：使用 writerows 一次性写入多行
                writer.writerows(rows)
                
        except Exception as e:
            logger.error(f"Failed to write batch to file: {e}")