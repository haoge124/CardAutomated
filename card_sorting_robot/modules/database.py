"""
数据库管理模块
负责管理卡片信息的存储和查询
使用SQLite数据库
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import shutil


class CardDatabase:
    """卡片数据库管理类"""

    def __init__(self, db_path: str = "data/cards.db"):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path

        # 确保数据目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """建立数据库连接"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        self.cursor = self.conn.cursor()

    def _create_tables(self):
        """创建数据库表"""
        # 卡片信息表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_number TEXT NOT NULL,
                confidence REAL NOT NULL,
                image_path TEXT,
                processed_image_path TEXT,
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'success',
                notes TEXT,
                UNIQUE(card_number, scan_time)
            )
        ''')

        # 统计信息表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE DEFAULT CURRENT_DATE,
                total_scanned INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                avg_confidence REAL DEFAULT 0.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建索引
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_card_number ON cards(card_number)
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_scan_time ON cards(scan_time)
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status ON cards(status)
        ''')

        self.conn.commit()

    def insert_card(self,
                    card_number: Optional[str],
                    confidence: float,
                    image_path: Optional[str] = None,
                    processed_image_path: Optional[str] = None,
                    status: str = 'success',
                    notes: Optional[str] = None) -> int:
        """
        插入卡片记录

        Args:
            card_number: 卡片番号
            confidence: 识别置信度
            image_path: 原始图像路径
            processed_image_path: 处理后图像路径
            status: 状态 ('success' 或 'failed')
            notes: 备注信息

        Returns:
            插入记录的ID
        """
        self.cursor.execute('''
            INSERT INTO cards (card_number, confidence, image_path,
                             processed_image_path, status, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (card_number, confidence, image_path, processed_image_path, status, notes))

        self.conn.commit()
        return self.cursor.lastrowid

    def get_card_by_id(self, card_id: int) -> Optional[Dict]:
        """
        根据ID获取卡片记录

        Args:
            card_id: 卡片ID

        Returns:
            卡片信息字典，如果不存在返回None
        """
        self.cursor.execute('SELECT * FROM cards WHERE id = ?', (card_id,))
        row = self.cursor.fetchone()

        if row:
            return dict(row)
        return None

    def get_cards_by_number(self, card_number: str) -> List[Dict]:
        """
        根据卡片番号获取所有记录

        Args:
            card_number: 卡片番号

        Returns:
            卡片信息列表
        """
        self.cursor.execute('SELECT * FROM cards WHERE card_number = ?', (card_number,))
        rows = self.cursor.fetchall()

        return [dict(row) for row in rows]

    def get_recent_cards(self, limit: int = 100) -> List[Dict]:
        """
        获取最近扫描的卡片

        Args:
            limit: 返回的记录数量

        Returns:
            卡片信息列表
        """
        self.cursor.execute('''
            SELECT * FROM cards
            ORDER BY scan_time DESC
            LIMIT ?
        ''', (limit,))
        rows = self.cursor.fetchall()

        return [dict(row) for row in rows]

    def get_cards_by_status(self, status: str) -> List[Dict]:
        """
        根据状态获取卡片

        Args:
            status: 状态 ('success' 或 'failed')

        Returns:
            卡片信息列表
        """
        self.cursor.execute('SELECT * FROM cards WHERE status = ?', (status,))
        rows = self.cursor.fetchall()

        return [dict(row) for row in rows]

    def update_card_status(self, card_id: int, status: str, notes: Optional[str] = None):
        """
        更新卡片状态

        Args:
            card_id: 卡片ID
            status: 新状态
            notes: 备注信息
        """
        if notes:
            self.cursor.execute('''
                UPDATE cards
                SET status = ?, notes = ?
                WHERE id = ?
            ''', (status, notes, card_id))
        else:
            self.cursor.execute('''
                UPDATE cards
                SET status = ?
                WHERE id = ?
            ''', (status, card_id))

        self.conn.commit()

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        stats = {}

        # 总数
        self.cursor.execute('SELECT COUNT(*) as total FROM cards')
        stats['total'] = self.cursor.fetchone()['total']

        # 成功数
        self.cursor.execute("SELECT COUNT(*) as success FROM cards WHERE status = 'success'")
        stats['success'] = self.cursor.fetchone()['success']

        # 失败数
        self.cursor.execute("SELECT COUNT(*) as failed FROM cards WHERE status = 'failed'")
        stats['failed'] = self.cursor.fetchone()['failed']

        # 平均置信度
        self.cursor.execute("SELECT AVG(confidence) as avg_conf FROM cards WHERE status = 'success'")
        avg_conf = self.cursor.fetchone()['avg_conf']
        stats['avg_confidence'] = round(avg_conf, 4) if avg_conf else 0.0

        # 成功率
        if stats['total'] > 0:
            stats['success_rate'] = round(stats['success'] / stats['total'] * 100, 2)
        else:
            stats['success_rate'] = 0.0

        # 不重复的卡片数
        self.cursor.execute("SELECT COUNT(DISTINCT card_number) as unique_cards FROM cards WHERE status = 'success'")
        stats['unique_cards'] = self.cursor.fetchone()['unique_cards']

        return stats

    def search_cards(self,
                     keyword: Optional[str] = None,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     min_confidence: Optional[float] = None) -> List[Dict]:
        """
        搜索卡片

        Args:
            keyword: 卡片番号关键词
            start_date: 开始日期
            end_date: 结束日期
            min_confidence: 最小置信度

        Returns:
            卡片信息列表
        """
        query = 'SELECT * FROM cards WHERE 1=1'
        params = []

        if keyword:
            query += ' AND card_number LIKE ?'
            params.append(f'%{keyword}%')

        if start_date:
            query += ' AND scan_time >= ?'
            params.append(start_date)

        if end_date:
            query += ' AND scan_time <= ?'
            params.append(end_date)

        if min_confidence is not None:
            query += ' AND confidence >= ?'
            params.append(min_confidence)

        query += ' ORDER BY scan_time DESC'

        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()

        return [dict(row) for row in rows]

    def delete_card(self, card_id: int):
        """
        删除卡片记录

        Args:
            card_id: 卡片ID
        """
        self.cursor.execute('DELETE FROM cards WHERE id = ?', (card_id,))
        self.conn.commit()

    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """
        备份数据库

        Args:
            backup_path: 备份文件路径，如果为None则自动生成

        Returns:
            备份文件路径
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(os.path.dirname(self.db_path), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, f'cards_backup_{timestamp}.db')

        # 关闭当前连接
        self.close()

        # 复制数据库文件
        shutil.copy2(self.db_path, backup_path)

        # 重新连接
        self._connect()

        return backup_path

    def clear_all_data(self):
        """清空所有数据（谨慎使用）"""
        self.cursor.execute('DELETE FROM cards')
        self.cursor.execute('DELETE FROM statistics')
        self.conn.commit()

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def __del__(self):
        """析构函数"""
        self.close()


def create_database_from_config(config: dict) -> CardDatabase:
    """
    从配置创建数据库实例

    Args:
        config: 完整配置字典

    Returns:
        CardDatabase实例
    """
    db_config = config.get('database', {})
    db_path = db_config.get('path', 'data/cards.db')

    return CardDatabase(db_path)


if __name__ == "__main__":
    # 测试代码
    print("测试数据库模块...")

    with CardDatabase("test_cards.db") as db:
        # 插入测试数据
        card_id = db.insert_card(
            card_number="TEST-12345",
            confidence=0.95,
            image_path="test/image.jpg",
            status="success"
        )
        print(f"插入卡片ID: {card_id}")

        # 查询
        card = db.get_card_by_id(card_id)
        print(f"查询结果: {card}")

        # 统计
        stats = db.get_statistics()
        print(f"统计信息: {stats}")

        # 备份
        backup_path = db.backup_database()
        print(f"数据库已备份到: {backup_path}")

    print("测试完成")
