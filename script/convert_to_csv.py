import os
import pandas as pd
from datetime import datetime
# 定义CSV字段
CSV_HEADERS = [
    "ioc_value",
    "ioc_type",
    "threat_type",
    "malware",
    "malware_alias",
    "malware_printable",
    "first_seen_utc",
    "last_seen_utc",
    "confidence_level",
    "reference",
    "tags",
    "anonymous",
    "reporter",
    "source"
      ]

def convert_to_csv(data, output_dir, source='unknown'):
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 总CSV文件路径
    total_csv_path = os.path.join(output_dir, "threat_intel_total.csv")

    # 读取现有数据
    existing_df = pd.DataFrame(columns=CSV_HEADERS)
    if os.path.exists(total_csv_path):
        existing_df = pd.read_csv(total_csv_path)
        
    # 转换新数据为DataFrame
    new_data = [{header: item.get(header, '') for header in CSV_HEADERS} for item in data]
    new_df = pd.DataFrame(new_data)
    new_df['source'] = source
    
    # 合并数据
    if not existing_df.empty:
        # 更新现有记录的last_seen_utc
        existing_df.loc[
            existing_df['ioc_value'].isin(new_df['ioc_value']) &
            existing_df['ioc_type'].isin(new_df['ioc_type']),
            'last_seen_utc'
        ] = datetime.now().strftime('%Y/%m/%d')
        # 合并新旧数据
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        # 去重，保留最后出现的记录
        subset_cols = [col for col in CSV_HEADERS if col not in ['first_seen_utc', 'last_seen_utc']]
        combined_df = combined_df.drop_duplicates(subset=subset_cols, keep='first')
    else:
        combined_df = new_df
    
    # 保存到CSV
    combined_df.to_csv(total_csv_path, index=False, encoding='utf-8')
    
    print(f"Successfully appended data to {total_csv_path}")

if __name__ == "__main__":
    # 示例数据
    sample_data = [
        {
            "ioc_value": "196.251.86.105:2404",
            "ioc_type": "ip:port",
            "threat_type": "botnet_cc",
            "malware": "win.remcos",
            "malware_alias": "RemcosRAT,Remvio,Socmer",
            "malware_printable": "Remcos",
            "first_seen_utc": "2025-03-28 05:40:23",
            "last_seen_utc": None,
            "confidence_level": 75,
            "reference": "https://bazaar.abuse.ch/sample/2edffaa16ba62436a4744e31d76dfaba8748534e4d6c752ca5b11949c25a4a7a/",
            "tags": "remcos",
            "anonymous": "0",
            "reporter": "abuse_ch"
        }
    ]
    
    # 设置输出目录
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'ti_collections')
    
    # 转换并保存为CSV
    convert_to_csv(sample_data, output_dir)