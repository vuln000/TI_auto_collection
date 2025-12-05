import httpx
import json
import logging
import asyncio
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
import pandas as pd
import io

logger = logging.getLogger("FeedFetcher")


class FeedFetcher:
    """
    Feed获取器类，负责从不同类型的数据源获取数据
    支持MISP manifest类型、CSV、Text和JSON类型feed
    """
    
    def __init__(self, fetcher_config: Dict[str, Any] = None, writer = None):
            """
            :param writer: FeedWriter 实例
            """
            self.http_client = None
            self.writer = writer  # <--- 保存 writer 实例
            self.describe_file = fetcher_config["describe_file"]
            self.concurrency = fetcher_config["concurrency"]
            self.timeout = fetcher_config["timeout"]
            self.time_range_days = fetcher_config["time_range_days"]
            self.user_agent = fetcher_config.get("user_agent", "FinalThreatFeed/1.0")
            self.headers = {"User-Agent": self.user_agent}
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(self.describe_file), exist_ok=True)
            self._init_describe_file()
            self._init_misp_download_record()

    def _init_describe_file(self):
        """
        初始化情报描述CSV文件，记录所有下载的情报信息
        """
        if not os.path.exists(self.describe_file):
            with open(self.describe_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'download_time',      # 下载时间
                    'name',               # 情报源名称
                    'source_format',      # 情报源类型
                    'url',                # 源URL
                    'event_uuid',         # MISP事件UUID（如果适用）
                    'data_type',          # 数据类型
                    'data_size',          # 数据大小
                    'threat_level',       # 威胁级别（如果适用）
                    'event_date'          # 事件日期（如果适用）
                ])
    
    def _init_misp_download_record(self):
        """
        初始化MISP下载记录，用于检查是否重复下载
        """
        # 从描述文件中提取已下载的MISP UUID
        self.misp_downloaded_uuids = set()
        try:
            with open(self.describe_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['source_format'] == 'misp' and row['event_uuid']:
                        self.misp_downloaded_uuids.add(row['event_uuid'])
        except Exception as e:
            logger.error(f"Failed to initialize MISP download record: {e}")
    
    def _record_intelligence(self, record_data: Dict):
        """
        记录情报到描述文件
        :param record_data: 情报记录数据
        """
        try:
            with open(self.describe_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # 确保所有字段都存在，不存在的字段用空字符串填充
                writer.writerow([
                    record_data.get('download_time', ''),
                    record_data.get('name', ''),
                    record_data.get('source_format', ''),
                    record_data.get('url', ''),
                    record_data.get('event_uuid', ''),
                    record_data.get('data_type', ''),
                    record_data.get('data_size', ''),
                    record_data.get('threat_level', ''),
                    record_data.get('event_date', '')
                ])
            # 如果是MISP情报，更新已下载UUID集合
            if record_data.get('source_format') == 'misp' and record_data.get('event_uuid'):
                self.misp_downloaded_uuids.add(record_data['event_uuid'])
        except Exception as e:
            logger.error(f"Failed to record intelligence: {e}")
    
    async def _init_http_client(self):
        """
        初始化HTTP客户端
        """
        if not self.http_client:
            self.http_client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers,
                follow_redirects=True
            )
        return self.http_client
    
    async def _close_http_client(self):
        """
        关闭HTTP客户端
        """
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
    
    async def _fetch_single_file(self, url: str, name: str) -> str:
        """
        通用的单文件下载方法
        
        :param url: 下载URL
        :param name: feed名称
        :return: 下载的文件内容
        """
        client = await self._init_http_client()
        logger.info(f"[{name}] Fetching: {url}")
        resp = await client.get(url)
        resp.raise_for_status()
        content = resp.text
        logger.info(f"[{name}] Downloaded {len(content)} bytes")
        return content
    
    async def _process_misp_feed(self, feed_cfg: Dict) -> List[Dict]:
        """
        处理MISP格式的feed，避免重复下载同一UUID的事件
        
        :param feed_cfg: feed配置
        :return: 下载并解析后的有效事件列表
        """
        name = feed_cfg.get("name")
        base_url = feed_cfg.get("url")
        
        # 传统的MISP manifest方式
        manifest_url = f"{base_url}/manifest.json"
        client = await self._init_http_client()
        
        # 1. 下载Manifest
        logger.info(f"[{name}] Fetching Manifest: {manifest_url}")
        resp = await client.get(manifest_url)
        resp.raise_for_status()
        
        # 2. 解析Manifest
        try:
            manifest = resp.json()
        except json.JSONDecodeError:
            logger.error(f"[{name}] Invalid JSON in manifest")
            return []
        
        # 3. 基于时间和UUID的筛选策略
        days_back = self.time_range_days
        cutoff_date = datetime.now() - timedelta(days=days_back)
            
        target_urls = []
        target_uuids = []
        target_metas = []
        
        # 记录已存在的UUID数量
        existing_uuid_count = 0
        # 记录不符合时间范围的UUID数量
        invalid_date_count = 0
        # 记录不符合威胁等级的UUID数量
        invalid_tli_count = 0

        for uuid, meta in manifest.items():
            # 跳过已下载的UUID
            if uuid in self.misp_downloaded_uuids:
                existing_uuid_count += 1
                continue
            
            event_date = datetime.fromtimestamp(int(meta.get("timestamp")))
            if event_date < cutoff_date:
                invalid_date_count += 1
                continue
            
            tli = meta.get("threat_level_id")
            if tli not in feed_cfg.get("threat_level_id"):
                invalid_tli_count += 1
                continue
            
            event_url = f"{base_url}/{uuid}.json"
            target_urls.append(event_url)
            target_uuids.append(uuid)
            target_metas.append(meta)

        logger.info(f"[{name}] Found {len(manifest)} total events, will download {len(target_urls)} new events")
        
        # 4. 并发下载子文件
        semaphore = asyncio.Semaphore(self.concurrency)

        def find_all_attributes(data):
            """
            递归查找所有名为'Attribute'的键，并返回合并后的列表
            """
            attributes = []
            
            if isinstance(data, dict):
                for key, value in data.items():
                    if key == 'Attribute':
                        # 如果'Attribute'的值是列表，直接添加所有元素
                        if isinstance(value, list):
                            attributes.extend(value)
                        # 如果'Attribute'的值是单个字典，添加这个字典
                        elif isinstance(value, dict):
                            attributes.append(value)
                    # 递归处理嵌套结构
                    attributes.extend(find_all_attributes(value))
            elif isinstance(data, list):
                for item in data:
                    attributes.extend(find_all_attributes(item))
            return attributes
        
        async def fetch_child(url, uuid, meta):
            async with semaphore:
                r = await self.http_client.get(url)  # 注意：这里要用 self.http_client
                r.raise_for_status()
                event_data = r.json()
                 
                # 递归提取所有 Attribute 并推送到 Writer 队列
                attributes = find_all_attributes(event_data)
                attributes_filtered = []
                for attr in attributes:
                    if attr.get('to_ids') == False:
                        continue
                    attributes_filtered.append(attr)

                attribute_count = len(attributes_filtered)
            
                for attr in attributes_filtered:
                    # 异步放入队列，不会阻塞
                    await self.writer.enqueue_generic(name, attr)

                # 3. 记录情报元数据 (Describe File)
                download_time = datetime.now().isoformat()
                event_date = datetime.fromtimestamp(int(meta.get("timestamp"))).isoformat() if meta.get("timestamp") else ""
                
                self._record_intelligence({
                    'download_time': download_time,
                    'name': name,
                    'source_format': 'misp',
                    'url': url,
                    'event_uuid': uuid,
                    'data_type': 'json',
                    'data_size': attribute_count,  # 统计Attribute条数
                    'threat_level': meta.get("threat_level_id"),
                    'event_date': event_date
                })
                
                return event_data

        # 并发下载子文件，使用return_exceptions=True以收集所有结果（包括异常）
        child_tasks = [fetch_child(url, uuid, meta) for url, uuid, meta in zip(target_urls, target_uuids, target_metas)]
        results = await asyncio.gather(*child_tasks, return_exceptions=True)
        
        # 处理结果，分离成功和失败的任务
        valid_events = []
        failed_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 记录失败的任务信息
                failed_count += 1
                uuid = target_uuids[i] if i < len(target_uuids) else "unknown"
                logger.error(f"[{name}] Failed to process event {uuid}: {result}")
            elif result is not None:
                valid_events.append(result)
        
        logger.info(f"[{name}] Successfully downloaded {len(valid_events)} new events. Failed: {failed_count}")
        
        return valid_events
    
    async def _process_csv_feed(self, feed_cfg: Dict) -> str:
        """
        处理CSV格式的feed，支持重复下载
        使用pandas批量处理，提高性能
        
        :param feed_cfg: feed配置
        :return: 下载的文件内容
        """
        url = feed_cfg.get("url")
        name = feed_cfg.get("name")
        
        # 获取CSV特定配置
        csv_config = feed_cfg.get("csv_config", {})
        delimiter = csv_config.get("delimiter", ",")
        time_column = csv_config.get("time_column", None)
        time_format = csv_config.get("time_format", None)
        value_column = csv_config.get("value_column", 1)
        threat_type = csv_config.get("threat_type", "")
        comment_column = csv_config.get("comment_column", None)
        static_comment = csv_config.get("static_comment", None)
        jump_line = csv_config.get("jump_line", 0)
        # 下载文件
        content = await self._fetch_single_file(url, name)
        
        # 根据配置处理头部
        processed_lines = content.splitlines()
        filtered_lines = []

        # 删除空行和注释行
        for line in  processed_lines:
            if line.strip() and not line.startswith("#"):
                filtered_lines.append(line)

        if jump_line > 0:
            filtered_lines = filtered_lines[jump_line:]
        else:
            filtered_lines = filtered_lines
        # 统计情报条数（CSV行数）
        intelligence_count = len(filtered_lines)
        
        # 使用pandas批量处理CSV数据
        # 将处理后的行转换为字符串
        csv_content = "\n".join(filtered_lines)
        
        # 使用pandas读取CSV数据
        df = pd.read_csv(
            io.StringIO(csv_content),
            delimiter=delimiter,
            header=None,  # 没有标题行，所有行都是数据
            skip_blank_lines=True
        )
        
        # 确保列索引从1开始，与用户配置保持一致
        df.columns = range(1, len(df.columns) + 1)
        
        # 批量处理数据
        csv_dicts = []
        for _, row in df.iterrows():
            # 提取时间信息
            timestamp = ""
            if time_column and time_column in row:
                timestamp = pd.to_datetime(row[time_column], format=time_format).timestamp()
            else:
                timestamp = datetime.now().timestamp()
            # 提取值
            value = ""
            if value_column and value_column in row:
                value = str(row[value_column])
            
            conment = ""
            if comment_column and comment_column in row:
                conment = str(row[comment_column])
            if static_comment:
                conment = ",".join(static_comment)
            
            # 构建写入字典
            csv_dict = {
                'timestamp': timestamp,
                'feed_name': name,
                'type': threat_type,  # 使用配置中的threat_type作为type
                'value': value,
                'comment': conment,
            }
            csv_dicts.append(csv_dict)
            
            # 批量写入数据
            await self.writer.enqueue_generic(name, csv_dict)
        download_time = datetime.now().isoformat()
        # 记录情报信息
        self._record_intelligence({
            'download_time': download_time,
            'name': name,
            'source_format': 'csv',
            'url': url,
            'event_uuid': '',
            'data_type': 'csv',
            'data_size': intelligence_count,  # 统计CSV行数
            'threat_level': '',
            'event_date': ''
        })
        
        return content

    async def _process_text_feed(self, feed_cfg: Dict) -> str:
        """
        处理纯文本/正则提取格式的feed
        参考CSV处理方式，将数据清洗后入队
        
        :param feed_cfg: feed配置
        :return: 下载的文件内容
        """
        import re # 引入正则模块
        
        url = feed_cfg.get("url")
        name = feed_cfg.get("name")
        
        # 获取Text特定配置
        text_config = feed_cfg.get("text_config", {})
        regex_pattern = text_config.get("regex", None)
        ioc_type = text_config.get("ioc_type", "unknown") # 默认类型
        static_comment = text_config.get("static_comment", [])
        
        # 将静态标签转换为 comment 字段
        comment_str = ",".join(static_comment) if static_comment else ""
        
        # 下载文件
        content = await self._fetch_single_file(url, name)
        
        # 预编译正则对象
        pattern = re.compile(regex_pattern) if regex_pattern else None
        
        lines = content.splitlines()
        intelligence_count = 0
        
        # 遍历每一行进行处理
        for line in lines:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue
            
            value = line
            
            # 如果配置了正则，尝试提取
            if pattern:
                match = pattern.search(line)
                if match:
                    # 优先使用第一个捕获组，如果没有捕获组则使用整个匹配
                    value = match.group(1) if match.groups() else match.group(0)
                else:
                    # 如果正则不匹配，跳过此行
                    continue
            
            # 构建标准写入字典
            text_dict = {
                'timestamp': datetime.now().timestamp(), # 文本源通常没有单行时间戳，使用当前时间
                'feed_name': name,
                'type': ioc_type,
                'value': value,
                'comment': comment_str
            }
            
            # 入队，交给Writer写入collections.csv
            await self.writer.enqueue_generic(name, text_dict)
            intelligence_count += 1
            
        download_time = datetime.now().isoformat()
        
        # 记录情报信息
        self._record_intelligence({
            'download_time': download_time,
            'name': name,
            'source_format': 'text',
            'url': url,
            'event_uuid': '',
            'data_type': 'text',
            'data_size': intelligence_count,  # 统计有效提取的条数
            'threat_level': '',
            'event_date': ''
        })
        
        return content
    
    async def fetch_feed(self, feed_cfg: Dict) -> Any:
        """
        统一的feed获取入口方法
        根据feed类型调用相应的处理方法
        
        :param feed_cfg: feed配置
        :return: 获取的数据，可能是字符串、字典或列表
        """
        name = feed_cfg.get("name", "Unknown")
        source_format = feed_cfg.get("source_format", "").lower()
        
        logger.info(f"[{name}] Starting to fetch feed (Type: {source_format})...")
        
        try:
            if source_format == "misp":
                result = await self._process_misp_feed(feed_cfg)
            elif source_format == "csv":
                result = await self._process_csv_feed(feed_cfg)
            elif source_format == "text":
                result = await self._process_text_feed(feed_cfg)
            else:
                # 默认为文本处理
                logger.warning(f"[{name}] Unknown format '{source_format}', treating as text")
                result = await self._process_text_feed(feed_cfg)
            
            logger.info(f"[{name}] Successfully fetched feed")
            return result

        except Exception as e:
            logger.error(f"[{name}] Failed to fetch feed: {e}")
            raise
        finally:
            # 注意：这里不关闭HTTP客户端，以便在多个feed之间复用
            pass
    
    async def __aenter__(self):
        """支持异步上下文管理器协议"""
        await self._init_http_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """支持异步上下文管理器协议"""
        await self._close_http_client()
