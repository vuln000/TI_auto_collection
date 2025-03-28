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
        else:
            print('Invalid JSON format')
    else:
        print(f'Failed to download {url}')

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
        else:
            print('No domains file found in extracted directory')
    else:
        print(f'Failed to download {url}')

# 主函数
def main():
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'ti_collections')
    os.makedirs(output_dir, exist_ok=True)
    process_cryptojacking(cryptojacking_url, output_dir)    
    process_threatfox(threatfox_url, output_dir)
    print('All done!')
if __name__ == '__main__':
    main()