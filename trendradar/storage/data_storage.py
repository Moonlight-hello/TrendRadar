# coding=utf-8
"""
大宗商品数据存储

扩展SQLite数据库以存储价格、库存、产量等数据
"""

import sqlite3
import json
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path

from trendradar.data.base import DataPoint


class DataStorage:
    """大宗商品数据存储类"""

    def __init__(self, db_path: str):
        """
        初始化数据存储

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path

        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # ═══════════════════════════════════════════════════════
        # 1. 通用数据表（所有大宗商品数据）
        # ═══════════════════════════════════════════════════════
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS commodity_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            date DATE NOT NULL,
            value REAL NOT NULL,
            category TEXT NOT NULL,
            data_type TEXT,
            product TEXT NOT NULL,
            unit TEXT,
            region TEXT DEFAULT 'China',
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 索引优化
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_commodity_date
        ON commodity_data(product, category, date)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_commodity_source
        ON commodity_data(source_id, date)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_commodity_product
        ON commodity_data(product, date DESC)
        """)

        # ═══════════════════════════════════════════════════════
        # 2. 数据源记录表（跟踪数据采集状态）
        # ═══════════════════════════════════════════════════════
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_fetch_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            fetch_time TIMESTAMP NOT NULL,
            status TEXT NOT NULL,
            data_count INTEGER DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_fetch_log_source
        ON data_fetch_log(source_id, fetch_time DESC)
        """)

        conn.commit()
        conn.close()

        print(f"✓ 数据库初始化完成: {self.db_path}")

    def save(self, data_points: List[DataPoint]) -> int:
        """
        保存数据点列表

        Args:
            data_points: 数据点列表

        Returns:
            保存的数据条数（新增 + 更新）
        """
        if not data_points:
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0
        updated_count = 0

        for dp in data_points:
            # 检查是否已存在
            cursor.execute("""
            SELECT id FROM commodity_data
            WHERE source_id=? AND date=? AND product=?
            """, (dp.source_id, dp.date.strftime("%Y-%m-%d"), dp.product))

            existing = cursor.fetchone()

            metadata_json = json.dumps(dp.metadata, ensure_ascii=False) if dp.metadata else None

            if existing:
                # 更新
                cursor.execute("""
                UPDATE commodity_data
                SET value=?, unit=?, metadata=?
                WHERE id=?
                """, (dp.value, dp.unit, metadata_json, existing[0]))
                updated_count += 1
            else:
                # 插入
                cursor.execute("""
                INSERT INTO commodity_data
                (source_id, date, value, category, data_type, product, unit, region, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dp.source_id,
                    dp.date.strftime("%Y-%m-%d"),
                    dp.value,
                    dp.category,
                    dp.data_type,
                    dp.product,
                    dp.unit,
                    dp.region,
                    metadata_json
                ))
                saved_count += 1

        conn.commit()
        conn.close()

        total = saved_count + updated_count
        print(f"✓ 数据保存完成: 新增{saved_count}条, 更新{updated_count}条")
        return total

    def log_fetch(self, source_id: str, status: str, record_count: int = 0, error_message: str = None):
        """
        记录数据采集日志

        Args:
            source_id: 数据源ID
            status: 状态（success/failed）
            record_count: 数据条数
            error_message: 错误信息
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO data_fetch_log
        (source_id, fetch_time, status, data_count, error_message)
        VALUES (?, ?, ?, ?, ?)
        """, (
            source_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status,
            record_count,
            error_message
        ))

        conn.commit()
        conn.close()

    def get_last_fetch_log(self, source_id: str) -> Optional[Dict]:
        """
        获取数据源的最后一次采集记录

        Args:
            source_id: 数据源ID

        Returns:
            最后一次采集记录，包含 fetch_time, status, record_count
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT fetch_time, status, data_count, error_message
        FROM data_fetch_log
        WHERE source_id=?
        ORDER BY fetch_time DESC
        LIMIT 1
        """, (source_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "fetch_time": datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S"),
            "status": row[1],
            "record_count": row[2],
            "error_message": row[3]
        }

    def query(
        self,
        product: str,
        category: str,
        start_date: datetime,
        end_date: datetime,
        data_type: Optional[str] = None
    ) -> List[DataPoint]:
        """
        查询数据

        Args:
            product: 产品（steel/copper/aluminum等）
            category: 数据类别（price/inventory/production等）
            start_date: 开始日期
            end_date: 结束日期
            data_type: 数据类型（可选）

        Returns:
            数据点列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        sql = """
        SELECT source_id, date, value, category, data_type, product, unit, region, metadata
        FROM commodity_data
        WHERE product=? AND category=?
        AND date BETWEEN ? AND ?
        """
        params = [
            product,
            category,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        ]

        if data_type:
            sql += " AND data_type=?"
            params.append(data_type)

        sql += " ORDER BY date DESC"

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        # 转换为DataPoint对象
        data_points = []
        for row in rows:
            metadata = json.loads(row[8]) if row[8] else {}

            dp = DataPoint(
                source_id=row[0],
                date=datetime.strptime(row[1], "%Y-%m-%d"),
                value=row[2],
                category=row[3],
                data_type=row[4],
                product=row[5],
                unit=row[6],
                region=row[7],
                metadata=metadata
            )
            data_points.append(dp)

        return data_points

    def get_latest(
        self,
        product: str,
        category: str,
        data_type: Optional[str] = None
    ) -> Optional[DataPoint]:
        """
        获取最新数据

        Args:
            product: 产品
            category: 数据类别
            data_type: 数据类型（可选）

        Returns:
            最新数据点
        """
        # 查询最近30天的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        results = self.query(product, category, start_date, end_date, data_type)

        return results[0] if results else None

    def get_products(self) -> List[str]:
        """获取所有产品列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT DISTINCT product FROM commodity_data
        ORDER BY product
        """)

        products = [row[0] for row in cursor.fetchall()]

        conn.close()
        return products

    def get_categories(self, product: str) -> List[str]:
        """获取产品的所有数据类别"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT DISTINCT category FROM commodity_data
        WHERE product=?
        ORDER BY category
        """, (product,))

        categories = [row[0] for row in cursor.fetchall()]

        conn.close()
        return categories

    def get_statistics(self) -> Dict:
        """获取数据库统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 总数据量
        cursor.execute("SELECT COUNT(*) FROM commodity_data")
        total_count = cursor.fetchone()[0]

        # 数据源数量
        cursor.execute("SELECT COUNT(DISTINCT source_id) FROM commodity_data")
        source_count = cursor.fetchone()[0]

        # 按产品统计
        cursor.execute("""
        SELECT product, COUNT(*) as count
        FROM commodity_data
        GROUP BY product
        ORDER BY count DESC
        """)
        by_product = dict(cursor.fetchall())

        # 按类别统计
        cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM commodity_data
        GROUP BY category
        ORDER BY count DESC
        """)
        by_category = dict(cursor.fetchall())

        # 按数据源统计
        cursor.execute("""
        SELECT source_id, COUNT(*) as count
        FROM commodity_data
        GROUP BY source_id
        ORDER BY count DESC
        """)
        by_source = dict(cursor.fetchall())

        # 最新数据日期
        cursor.execute("SELECT MAX(date) FROM commodity_data")
        latest_date = cursor.fetchone()[0] or "无数据"

        # 最早数据日期
        cursor.execute("SELECT MIN(date) FROM commodity_data")
        earliest_date = cursor.fetchone()[0] or "无数据"

        conn.close()

        return {
            "total_count": total_count,
            "source_count": source_count,
            "by_product": by_product,
            "by_category": by_category,
            "by_source": by_source,
            "latest_date": latest_date,
            "earliest_date": earliest_date
        }

    def cleanup_old_data(self, days: int = 365):
        """
        清理旧数据

        Args:
            days: 保留天数
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        DELETE FROM commodity_data
        WHERE date < ?
        """, (cutoff_date,))

        deleted_count = cursor.rowcount

        conn.commit()
        conn.close()

        print(f"✓ 清理完成: 删除{deleted_count}条旧数据（早于{cutoff_date}）")

    def close(self):
        """关闭数据库连接"""
        # SQLite 是文件数据库，每次操作都打开关闭连接，这里不需要额外操作
        pass
