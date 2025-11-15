#!/usr/bin/env python3
"""
数据库管理工具
用于查询和管理卡片数据库
"""

import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_loader import get_config
from modules.database import create_database_from_config


def show_statistics(db):
    """显示统计信息"""
    stats = db.get_statistics()

    print("="*60)
    print("数据库统计信息")
    print("="*60)
    print(f"总记录数: {stats['total']}")
    print(f"识别成功: {stats['success']} ({stats['success_rate']:.1f}%)")
    print(f"识别失败: {stats['failed']}")
    print(f"不重复卡片: {stats['unique_cards']}")
    print(f"平均置信度: {stats['avg_confidence']:.4f}")
    print("="*60)


def show_recent_cards(db, limit=10):
    """显示最近的卡片记录"""
    cards = db.get_recent_cards(limit)

    print(f"\n最近 {limit} 条记录：")
    print("-"*100)
    print(f"{'ID':<5} {'卡片番号':<15} {'置信度':<10} {'状态':<10} {'扫描时间':<20}")
    print("-"*100)

    for card in cards:
        print(f"{card['id']:<5} {card['card_number'] or 'N/A':<15} "
              f"{card['confidence']:<10.4f} {card['status']:<10} {card['scan_time']:<20}")

    print("-"*100)


def search_cards(db, keyword=None, start_date=None, end_date=None, min_confidence=None):
    """搜索卡片"""
    cards = db.search_cards(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        min_confidence=min_confidence
    )

    print(f"\n搜索结果（共 {len(cards)} 条）：")
    print("-"*100)
    print(f"{'ID':<5} {'卡片番号':<15} {'置信度':<10} {'状态':<10} {'扫描时间':<20}")
    print("-"*100)

    for card in cards:
        print(f"{card['id']:<5} {card['card_number'] or 'N/A':<15} "
              f"{card['confidence']:<10.4f} {card['status']:<10} {card['scan_time']:<20}")

    print("-"*100)


def export_to_csv(db, output_file):
    """导出数据到CSV文件"""
    import csv

    cards = db.get_recent_cards(limit=100000)  # 获取所有记录

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'id', 'card_number', 'confidence', 'status', 'scan_time',
            'image_path', 'processed_image_path', 'notes'
        ])
        writer.writeheader()
        writer.writerows(cards)

    print(f"✓ 数据已导出到: {output_file}")
    print(f"  共 {len(cards)} 条记录")


def backup_database(db):
    """备份数据库"""
    backup_path = db.backup_database()
    print(f"✓ 数据库已备份到: {backup_path}")


def delete_card(db, card_id):
    """删除卡片记录"""
    card = db.get_card_by_id(card_id)
    if not card:
        print(f"❌ 未找到 ID 为 {card_id} 的记录")
        return

    print(f"将删除以下记录：")
    print(f"  ID: {card['id']}")
    print(f"  卡片番号: {card['card_number']}")
    print(f"  扫描时间: {card['scan_time']}")

    confirm = input("确认删除？(y/n): ")
    if confirm.lower() == 'y':
        db.delete_card(card_id)
        print("✓ 记录已删除")
    else:
        print("已取消")


def clear_database(db):
    """清空数据库"""
    print("⚠️  警告：此操作将删除所有数据！")
    confirm = input("确认清空数据库？输入 'DELETE ALL' 确认: ")

    if confirm == 'DELETE ALL':
        db.clear_all_data()
        print("✓ 数据库已清空")
    else:
        print("已取消")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='卡片数据库管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 统计信息
    subparsers.add_parser('stats', help='显示统计信息')

    # 显示最近记录
    recent_parser = subparsers.add_parser('recent', help='显示最近的记录')
    recent_parser.add_argument('-n', '--num', type=int, default=10, help='显示的记录数量')

    # 搜索
    search_parser = subparsers.add_parser('search', help='搜索卡片')
    search_parser.add_argument('-k', '--keyword', type=str, help='卡片番号关键词')
    search_parser.add_argument('-s', '--start-date', type=str, help='开始日期 (YYYY-MM-DD)')
    search_parser.add_argument('-e', '--end-date', type=str, help='结束日期 (YYYY-MM-DD)')
    search_parser.add_argument('-c', '--confidence', type=float, help='最小置信度')

    # 导出
    export_parser = subparsers.add_parser('export', help='导出数据到CSV')
    export_parser.add_argument('-o', '--output', type=str, required=True, help='输出文件路径')

    # 备份
    subparsers.add_parser('backup', help='备份数据库')

    # 删除
    delete_parser = subparsers.add_parser('delete', help='删除指定记录')
    delete_parser.add_argument('id', type=int, help='记录ID')

    # 清空
    subparsers.add_parser('clear', help='清空数据库（危险操作）')

    args = parser.parse_args()

    # 加载配置和数据库
    config = get_config()
    db = create_database_from_config(config.config)

    try:
        if args.command == 'stats':
            show_statistics(db)

        elif args.command == 'recent':
            show_recent_cards(db, args.num)

        elif args.command == 'search':
            search_cards(db, args.keyword, args.start_date, args.end_date, args.confidence)

        elif args.command == 'export':
            export_to_csv(db, args.output)

        elif args.command == 'backup':
            backup_database(db)

        elif args.command == 'delete':
            delete_card(db, args.id)

        elif args.command == 'clear':
            clear_database(db)

        else:
            parser.print_help()

    finally:
        db.close()


if __name__ == "__main__":
    main()
