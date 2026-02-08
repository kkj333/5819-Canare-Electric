"""
pytest 設定ファイル
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加（scripts/ のインポートを可能にする）
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
