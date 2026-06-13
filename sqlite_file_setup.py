import os
import sqlite3
import json
import uuid
import getpass
import paths_setup as psp
import toolsfile_json as tfj


def get_current_user():
    """获取当前系统用户名"""
    return getpass.getuser()


def get_sqlite_folder():
    """获取 SQLite 数据库文件夹路径"""
    local_path = psp.local_path_get()
    sqlite_folder = os.path.join(local_path, "SQLite_file")
    os.makedirs(sqlite_folder, exist_ok=True)
    return sqlite_folder


def get_user_config_path():
    """获取用户配置文件路径"""
    users_path = psp.users_path_get()
    username = get_current_user()
    user_config = os.path.join(users_path, username, "db_config.json")
    os.makedirs(os.path.dirname(user_config), exist_ok=True)
    return user_config


def get_current_user_db_uuid():
    """获取当前用户绑定的数据库 UUID"""
    config_path = get_user_config_path()
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            db_uuid = config.get('current_db_uuid')
            if db_uuid:
                print(f"✓ 当前用户: {get_current_user()}")
                print(f"✓ 使用数据库 UUID: {db_uuid}")
                return db_uuid
    
    db_uuid = str(uuid.uuid4())
    save_user_db_uuid(db_uuid)
    print(f"✓ 当前用户: {get_current_user()}")
    print(f"✓ 创建新数据库 UUID: {db_uuid}")
    return db_uuid


def save_user_db_uuid(db_uuid):
    """保存用户的数据库 UUID 配置"""
    config_path = get_user_config_path()
    config = {
        'current_db_uuid': db_uuid,
        'username': get_current_user()
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_user_db_path(db_uuid=None):
    """获取用户数据库文件路径"""
    if db_uuid is None:
        db_uuid = get_current_user_db_uuid()
    
    sqlite_folder = get_sqlite_folder()
    db_path = os.path.join(sqlite_folder, f"tools_{db_uuid}.db")
    
    return db_path


def list_all_databases():
    """列出所有可用的数据库"""
    sqlite_folder = get_sqlite_folder()
    
    if not os.path.exists(sqlite_folder):
        return []
    
    databases = []
    for file in os.listdir(sqlite_folder):
        if file.endswith('.db'):
            db_uuid = file.replace('tools_', '').replace('.db', '')
            db_path = os.path.join(sqlite_folder, file)
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM tools_index')
                tool_count = cursor.fetchone()[0]
                conn.close()
                
                databases.append({
                    'uuid': db_uuid,
                    'path': db_path,
                    'tool_count': tool_count,
                    'filename': file
                })
            except:
                databases.append({
                    'uuid': db_uuid,
                    'path': db_path,
                    'tool_count': 0,
                    'filename': file
                })
    
    return databases


def switch_database(db_uuid):
    """切换到指定的数据库"""
    save_user_db_uuid(db_uuid)
    db_path = get_user_db_path(db_uuid)
    
    print(f"✓ 已切换到数据库: {db_uuid}")
    print(f"✓ 数据库路径: {db_path}")
    
    return db_path


def init_database(db_path=None):
    """初始化数据库，创建表结构和索引"""
    if db_path is None:
        db_path = get_user_db_path()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tools_index (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            tag TEXT DEFAULT '',
            matchClass TEXT DEFAULT '[]',
            main_file TEXT NOT NULL,
            icon_file TEXT,
            help_file TEXT,
            category TEXT DEFAULT '',
            has_icon INTEGER DEFAULT 0,
            has_help INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id TEXT NOT NULL,
            is_installed INTEGER DEFAULT 0,
            is_favorite INTEGER DEFAULT 0,
            usage_count INTEGER DEFAULT 0,
            is_enabled INTEGER DEFAULT 1,
            custom_tag TEXT DEFAULT '',
            last_used TEXT,
            FOREIGN KEY (tool_id) REFERENCES tools_index(id),
            UNIQUE(tool_id)
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tools_name ON tools_index(name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tools_tag ON tools_index(tag)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tools_matchClass ON tools_index(matchClass)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tools_category ON tools_index(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_tools_tool_id ON user_tools(tool_id)')
    
    conn.commit()
    conn.close()
    
    print(f"✓ 数据库初始化完成: {db_path}")
    return db_path


def check_database_for_duplicates(db_path=None):
    """检查数据库中是否有重复的工具"""
    if db_path is None:
        db_path = get_user_db_path()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查重复的 ID
    cursor.execute('''
        SELECT id, name, COUNT(*) as count 
        FROM tools_index 
        GROUP BY id 
        HAVING count > 1
    ''')
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"\n️  发现 {len(duplicates)} 个重复的工具 ID:")
        for dup in duplicates:
            print(f"  ID: {dup[0]}, 名称: {dup[1]}, 重复次数: {dup[2]}")
    else:
        print("\n✓ 数据库中没有重复的工具 ID")
    
    # 显示所有工具的 ID 和名称
    cursor.execute('SELECT id, name FROM tools_index ORDER BY name')
    all_tools = cursor.fetchall()
    print(f"\n数据库中共有 {len(all_tools)} 条记录:")
    for i, (tool_id, name) in enumerate(all_tools[:10], 1):
        print(f"  {i}. {name} (ID: {tool_id[:16]}...)")
    if len(all_tools) > 10:
        print(f"  ... 还有 {len(all_tools) - 10} 个工具")
    
    conn.close()
    return duplicates


def sync_tools_to_database(db_path=None):
    """
    从 JSON 文件同步所有工具到数据库
    
    策略：
    1. 保存用户配置（安装/收藏状态）
    2. 清空并重建 tools_index 表
    3. 恢复用户配置
    """
    if db_path is None:
        db_path = get_user_db_path()
    
    init_database(db_path)
    
    print("正在从 JSON 文件加载工具...")
    all_tools = tfj.get_all_tools()
    
    if not all_tools:
        print(" 没有找到工具，清理数据库中的旧工具记录")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tools_index')
        cursor.execute('DELETE FROM user_tools')
        conn.commit()
        conn.close()
        print(" 已清空所有工具记录")
        return 0
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 第一步：保存当前用户配置（安装/收藏状态）
    cursor.execute('SELECT tool_id, is_installed, is_favorite, usage_count, last_used FROM user_tools')
    user_configs = {}
    for row in cursor.fetchall():
        user_configs[row[0]] = {
            'is_installed': row[1],
            'is_favorite': row[2],
            'usage_count': row[3],
            'last_used': row[4]
        }
    
    installed_count = sum(1 for c in user_configs.values() if c['is_installed'])
    favorite_count = sum(1 for c in user_configs.values() if c['is_favorite'])
    print(f"  已保存 {len(user_configs)} 个工具的用户配置")
    print(f"  其中：已安装 {installed_count} 个，已收藏 {favorite_count} 个")
    
    # 第二步：清空工具索引表
    cursor.execute('DELETE FROM tools_index')
    print("  已清空工具索引表")
    
    # 第三步：重新插入所有工具
    json_tool_ids = set()
    for tool in all_tools:
        tool_id = tool.get('id')
        if not tool_id:
            continue
        
        json_tool_ids.add(tool_id)
        
        name = tool.get('name', '')
        tag = tool.get('tag', '')
        matchClass = json.dumps(tool.get('matchClass', []), ensure_ascii=False)
        
        files = tool.get('files', {})
        main_file = files.get('main', '')
        icon_file = files.get('icon')
        help_file = files.get('help')
        
        category = ''
        if main_file:
            parts = main_file.split('/')
            if len(parts) > 1:
                category = '/'.join(parts[:-1])
        
        has_icon = 1 if icon_file else 0
        has_help = 1 if help_file else 0
        
        cursor.execute('''
            INSERT INTO tools_index (
                id, name, tag, matchClass, main_file, 
                icon_file, help_file, category, has_icon, has_help
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (tool_id, name, tag, matchClass, main_file, 
              icon_file, help_file, category, has_icon, has_help))
        
        # 恢复用户配置（如果存在）或创建新记录
        if tool_id in user_configs:
            config = user_configs[tool_id]
            cursor.execute('''
                INSERT OR REPLACE INTO user_tools 
                (tool_id, is_installed, is_favorite, usage_count, last_used)
                VALUES (?, ?, ?, ?, ?)
            ''', (tool_id, config['is_installed'], config['is_favorite'], 
                  config['usage_count'], config['last_used']))
        else:
            cursor.execute('''
                INSERT OR IGNORE INTO user_tools (tool_id) VALUES (?)
            ''', (tool_id,))
    
    # 第四步：清理已删除工具的用户配置
    cursor.execute('SELECT tool_id FROM user_tools')
    all_user_tool_ids = set(row[0] for row in cursor.fetchall())
    deleted_tools = all_user_tool_ids - json_tool_ids
    
    if deleted_tools:
        print(f"  清理 {len(deleted_tools)} 个已删除工具的配置")
        cursor.execute('DELETE FROM user_tools WHERE tool_id IN ({})'.format(
            ','.join(['?'] * len(deleted_tools))
        ), list(deleted_tools))
    
    conn.commit()
    
    # 验证实际数量
    cursor.execute('SELECT COUNT(*) FROM tools_index')
    actual_count = cursor.fetchone()[0]
    
    # 验证用户配置恢复情况
    cursor.execute('SELECT COUNT(*), SUM(is_installed), SUM(is_favorite) FROM user_tools')
    row = cursor.fetchone()
    total_configs = row[0]
    installed_configs = row[1] or 0
    favorite_configs = row[2] or 0
    
    conn.close()
    
    print(f"成功同步 {actual_count} 个工具")
    print(f"用户配置：总计 {total_configs} 个，已安装 {installed_configs} 个，已收藏 {favorite_configs} 个")
    return actual_count


def search_tools(keyword=None, tag=None, matchClass=None, category=None, 
                 is_installed=None, is_favorite=None, db_path=None):
    """搜索工具"""
    if db_path is None:
        db_path = get_user_db_path()
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = '''
        SELECT t.*, u.is_installed, u.is_favorite, u.usage_count, 
               u.is_enabled, u.custom_tag, u.last_used
        FROM tools_index t
        LEFT JOIN user_tools u ON t.id = u.tool_id
        WHERE 1=1
    '''
    params = []
    
    if keyword:
        query += ' AND t.name LIKE ?'
        params.append(f'%{keyword}%')
    
    if tag:
        query += ' AND t.tag = ?'
        params.append(tag)
    
    if matchClass:
        query += ' AND t.matchClass LIKE ?'
        params.append(f'%"{matchClass}"%')
    
    if category:
        query += ' AND t.category LIKE ?'
        params.append(f'%{category}%')
    
    if is_installed is not None:
        query += ' AND u.is_installed = ?'
        params.append(is_installed)
    
    if is_favorite is not None:
        query += ' AND u.is_favorite = ?'
        params.append(is_favorite)
    
    query += ' ORDER BY t.name'
    
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return results


def get_tool_by_id(tool_id, db_path=None):
    """通过 UUID 获取工具详情"""
    if db_path is None:
        db_path = get_user_db_path()
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.*, u.is_installed, u.is_favorite, u.usage_count, 
               u.is_enabled, u.custom_tag, u.last_used
        FROM tools_index t
        LEFT JOIN user_tools u ON t.id = u.tool_id
        WHERE t.id = ?
    ''', (tool_id,))
    
    row = cursor.fetchone()
    result = dict(row) if row else None
    
    conn.close()
    return result


def get_all_tools_from_db(db_path=None):
    """获取数据库中所有工具"""
    return search_tools(db_path=db_path)


def update_tool_installation(tool_id, is_installed=1, db_path=None):
    """更新工具安装状态"""
    if db_path is None:
        db_path = get_user_db_path()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE user_tools 
        SET is_installed = ?
        WHERE tool_id = ?
    ''', (is_installed, tool_id))
    
    conn.commit()
    conn.close()


def update_tool_usage(tool_id, db_path=None):
    """更新工具使用次数"""
    if db_path is None:
        db_path = get_user_db_path()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE user_tools 
        SET usage_count = usage_count + 1,
            last_used = CURRENT_TIMESTAMP
        WHERE tool_id = ?
    ''', (tool_id,))
    
    conn.commit()
    conn.close()


def toggle_favorite(tool_id, db_path=None):
    """切换工具收藏状态"""
    if db_path is None:
        db_path = get_user_db_path()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT is_favorite FROM user_tools WHERE tool_id = ?', (tool_id,))
    row = cursor.fetchone()
    
    if row:
        new_state = 1 - row[0]
        cursor.execute('UPDATE user_tools SET is_favorite = ? WHERE tool_id = ?', 
                      (new_state, tool_id))
    else:
        new_state = 1
        cursor.execute('INSERT INTO user_tools (tool_id, is_favorite) VALUES (?, ?)', 
                      (tool_id, new_state))
    
    conn.commit()
    conn.close()
    
    return new_state


if __name__ == "__main__":
    print("=" * 60)
    print("检查数据库重复问题")
    print("=" * 60)
    
    db_path = get_user_db_path()
    print(f"\n数据库路径: {db_path}\n")
    
    # 检查重复
    check_database_for_duplicates(db_path)
    
    print("\n" + "=" * 60)
    print("现在同步工具")
    print("=" * 60)
    
    count = sync_tools_to_database(db_path)
    
    print("\n同步后再次检查:")
    check_database_for_duplicates(db_path)