"""
FinalThreatFeed - 开源威胁情报自动化搜集工具
主入口文件
"""

import sys
import asyncio
from src.core import CoreEngine

def main():
    """主函数"""
    try:
        # 创建核心引擎实例
        engine = CoreEngine()
        asyncio.run(engine.run_pipeline())
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()