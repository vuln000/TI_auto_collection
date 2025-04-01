import configparser
import requests
import tarfile
import os
from datetime import date
# 读取配置文件
config = configparser.ConfigParser()
config.read('config.ini')

# 获取URLs
cryptojacking_url = config['URLs']['cryptojacking']
threatfox_url = config['URLs']['threatfox']

# 处理tar.gz文件

# 处理threatfox情报
def process_threatfox(url, output_dir):
    response = requests.get(url)
    if response.status_code == 200:
        # 解析JSON数据
        data = response.json()
        # 确保数据是字典格式
        if isinstance(data, dict):
            # 处理每条威胁信息
            threat_data = []
            for key, value in data.items():
                if isinstance(value, list):
                    for item in value:
                        # 转换日期格式
                        if 'first_seen_utc' in item and item['first_seen_utc']:
                            item['first_seen_utc'] = item['first_seen_utc'].split()[0]
                        if 'last_seen_utc' in item and item['last_seen_utc']:
                            item['last_seen_utc'] = item['last_seen_utc'].split()[0]
                        threat_data.append(item)
            # 调用convert_to_csv函数
            from convert_to_csv import convert_to_csv
            convert_to_csv(threat_data, output_dir,source=url)
            print(f'Successfully processed {url} and saved to CSV in {output_dir}')
            # 更新README状态
            update_readme_status(url, 'success')
        else:
            print('Invalid JSON format')
    else:
        print(f'Failed to download {url}')
        update_readme_status(url, 'failed')

# 处理cryptojacking情报
def process_cryptojacking(url, output_dir):
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    # 下载tar.gz文件
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        # 获取文件名
        file_name = os.path.join(output_dir, os.path.basename(url))
        # 保存tar.gz文件
        with open(file_name, 'wb') as f:
            f.write(response.content)
        # 解压文件
        with tarfile.open(file_name, 'r:gz') as tar:
            tar.extractall(path=output_dir)
        # 获取解压后的目录名
        extracted_dir = os.path.join(output_dir, os.path.basename(url).replace('.tar.gz', ''))
        # 处理domain文件
        domain_file = os.path.join(extracted_dir, 'domains')
        if os.path.exists(domain_file):
            # 读取domain文件内容
            with open(domain_file, 'r') as f:
                domains = [line.strip().replace('0.0.0.0', '') for line in f if line.strip()]
            # 转换为标准数据结构
            threat_data = [
                {   
                    'ioc_value': domain,
                    'ioc_type': 'domain',
                    'threat_type': 'cryptojacking',
                    'tags': 'mining_pool',
                    'first_seen_utc': date.today().strftime('%Y/%m/%d'),
                    'confidence_level': 100
                }
                for i, domain in enumerate(domains)
            ]
            # 调用convert_to_csv函数
            from convert_to_csv import convert_to_csv
            convert_to_csv(threat_data, output_dir, source=url)
            # 删除解压目录
            import shutil
            shutil.rmtree(extracted_dir)
            # 删除tar.gz文件
            os.remove(file_name)
            print(f'Successfully processed {url} and saved to CSV in {output_dir}')
            # 更新README状态
            update_readme_status(url, 'success')
        else:
            print('No domains file found in extracted directory')
            update_readme_status(url, 'failed')
    else:
        print(f'Failed to download {url}')
        update_readme_status(url, 'failed')

def update_readme_status(source_url, status):
    """更新README.md文件中的状态信息"""
    import time
    readme_path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
    
    # 读取当前README内容
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已有状态表格
    if '## 数据更新状态' not in content:
        # 添加状态表格
        status_table = """
## 数据更新状态

| 数据源 | 最后更新时间 | 状态 |
|--------|------------|------|
"""
        content = content + status_table
    
    # 更新或添加状态行
    current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    status_line = f"| {source_url} | {current_time} | {'✅ 成功' if status == 'success' else '❌ 失败'} |"
    
    if f"| {source_url} |" in content:
        # 更新现有行
        import re
        content = re.sub(fr'\| {source_url} \|.*\|.*\|', status_line, content)
    else:
        # 添加新行
        content = content + '\n' + status_line
    
    # 写回文件
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)

# 获取统计信息
def update_statistics():
    import pandas as pd
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'ti_collections', 'threat_intel_total.csv')
    df = pd.read_csv(csv_path)
    total_count = len(df)
    ioc_type_counts = df['ioc_type'].value_counts().to_dict()
    source_counts = df['source'].value_counts().to_dict()
    
    # 生成统计信息文本
    stats_text = f"\n## 数据统计信息\n\n| 统计项 | 值 |\n|--------|----|\n| 总记录数 | {total_count} |\n\n### IOC类型统计\n\n| 类型 | 数量 |\n|------|------|\n" + '\n'.join([f'| {k} | {v} |' for k, v in ioc_type_counts.items()]) + "\n\n### 数据源统计\n\n| 数据源 | 数量 |\n|--------|------|\n" + '\n'.join([f'| {k} | {v} |' for k, v in source_counts.items()]) + "\n"
    
    # 更新README文件
    readme_path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 移除旧的统计信息
    if '## 数据统计信息' in content:
        content = content.split('## 数据统计信息')[0]
    
    # 添加新的统计信息
    content = content + stats_text
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return {
        'total_count': total_count,
        'ioc_type_counts': ioc_type_counts,
        'source_counts': source_counts
    }

def main():
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'ti_collections')
    os.makedirs(output_dir, exist_ok=True)
    process_cryptojacking(cryptojacking_url, output_dir)    
    process_threatfox(threatfox_url, output_dir)
    update_statistics()
    print('All done!')
if __name__ == '__main__':
    main()