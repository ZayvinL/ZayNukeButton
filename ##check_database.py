# -*- coding: UTF-8 -*-
"""
数据库诊断脚本 - 查看数据库中实际存储的数据
"""

import os
import json
import sqlite3

# 获取数据库路径
project_root = os.path.dirname(__file__)
config_path = os.path.join(project_root, 'users', 'liucx', 'db_config.json')

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
    db_uuid = config.get('current_db_uuid')

sqlite_folder = os.path.join(project_root, 'SQLite_file')
db_path = os.path.join(sqlite_folder, f"tools_{db_uuid}.db")

print("="*80)
print(f"数据库路径: {db_path}")
print("="*80)

if not os.path.exists(db_path):
    print(f"❌ 数据库文件不存在!")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. 查看表结构
print("\n📋 数据库表结构:")
print("-"*80)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"  表名: {table['name']}")
    cursor.execute(f"PRAGMA table_info({table['name']})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"    - {col['name']} ({col['type']})")

# 2. 查看 tools_index 表的统计数据
print("\n📊 tools_index 表统计:")
print("-"*80)
cursor.execute("SELECT COUNT(*) as count FROM tools_index")
total = cursor.fetchone()['count']
print(f"  总记录数: {total}")

# 3. 查看 matchClass 字段的实际存储格式
print("\n🔍 matchClass 字段示例（前10条）:")
print("-"*80)
cursor.execute("SELECT id, name, matchClass FROM tools_index LIMIT 10")
rows = cursor.fetchall()
for row in rows:
    print(f"  名称: {row['name']}")
    print(f"    matchClass: {row['matchClass']}")
    print(f"    类型: {type(row['matchClass'])}")
    print()

# 4. 查看 user_tools 表的统计数据
print("\n📊 user_tools 表统计:")
print("-"*80)
cursor.execute("SELECT COUNT(*) as count FROM user_tools")
total = cursor.fetchone()['count']
print(f"  总记录数: {total}")

cursor.execute("SELECT COUNT(*) as count FROM user_tools WHERE is_installed = 1")
installed = cursor.fetchone()['count']
print(f"  已安装 (is_installed=1): {installed}")

cursor.execute("SELECT COUNT(*) as count FROM user_tools WHERE is_installed = 0")
not_installed = cursor.fetchone()['count']
print(f"  未安装 (is_installed=0): {not_installed}")

# 5. 测试查询：查找包含 "None" 的工具
print("\n🔍 测试查询：matchClass 包含 'None' 的工具")
print("-"*80)
cursor.execute("""
    SELECT t.id, t.name, t.matchClass, u.is_installed
    FROM tools_index t
    LEFT JOIN user_tools u ON t.id = u.tool_id
    WHERE t.matchClass LIKE '%"None"%'
    LIMIT 5
""")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"  名称: {row['name']}")
        print(f"    matchClass: {row['matchClass']}")
        print(f"    is_installed: {row['is_installed']}")
        print()
else:
    print("  ❌ 未找到包含 'None' 的工具")

# 6. 查看所有不同的 matchClass 值
print("\n🔍 所有不同的 matchClass 值（前20个）:")
print("-"*80)
cursor.execute("SELECT DISTINCT matchClass FROM tools_index LIMIT 20")
rows = cursor.fetchall()
for i, row in enumerate(rows, 1):
    print(f"  {i}. {row['matchClass']}")

# 7. 查看一个完整工具的详细信息
print("\n🔍 完整工具示例（第一条记录）:")
print("-"*80)
cursor.execute("""
    SELECT t.*, u.is_installed, u.is_favorite, u.usage_count
    FROM tools_index t
    LEFT JOIN user_tools u ON t.id = u.tool_id
    LIMIT 1
""")
row = cursor.fetchone()
if row:
    print("  tools_index 表字段:")
    for key in row.keys():
        if key in ['id', 'name', 'tag', 'matchClass', 'main_file', 'icon_file', 'help_file', 'category']:
            print(f"    {key}: {row[key]}")
    
    print("\n  user_tools 表字段:")
    print(f"    is_installed: {row['is_installed']}")
    print(f"    is_favorite: {row['is_favorite']}")
    print(f"    usage_count: {row['usage_count']}")

conn.close()

print("\n" + "="*80)
print("诊断完成!")
print("="*80)