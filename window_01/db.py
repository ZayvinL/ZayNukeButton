# c:/Users/liucx/.nuke/MyButton/window_01/db.py
# -*- coding: UTF-8 -*-
"""数据库查询和缓存管理"""

import os
import sqlite3

# from PySide6.QtCore import QSize
# from PySide6.QtGui import QIcon, QPixmap, Qt

from qt_imports import QSize, QIcon, QPixmap, Qt

class FastDBQuery:
    """快速数据库查询器"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self._connection = None
    
    def _get_connection(self):
        if self._connection is None and self.db_path:
            if os.path.exists(self.db_path):
                self._connection = sqlite3.connect(self.db_path)
                self._connection.row_factory = sqlite3.Row
            else:
                raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")
        return self._connection
    
    def search_tools(self, search_params, is_installed_only=False, limit=10, offset=0):
        """
        搜索工具
        
        search_params: {
            'classes': ['Read', 'Write'],  # C=: 类别
            'labels': ['Python'],          # L=: 标签
            'paths': ['C:\\Tools'],        # P=: 路径
            'names': ['Notepad'],          # N=: 名称
            'keywords': ['test']           # 普通关键词（模糊搜索所有字段）
        }
        is_installed_only: 是否只搜索已安装的工具
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        # 是否只搜索已安装的工具
        if is_installed_only:
            conditions.append("u.is_installed = 1")
        
        # 类别搜索（精确匹配）
        if search_params.get('classes'):
            class_conditions = []
            for cls in search_params['classes']:
                class_conditions.append("t.matchClass LIKE ?")
                params.append(f'%"{cls}"%')
            conditions.append(f"({' OR '.join(class_conditions)})")
        
        # 标签搜索（模糊匹配）
        if search_params.get('labels'):
            label_conditions = []
            for label in search_params['labels']:
                label_conditions.append("t.tag LIKE ?")
                params.append(f'%{label}%')
            conditions.append(f"({' OR '.join(label_conditions)})")
        
        # 路径搜索（模糊匹配）
        if search_params.get('paths'):
            path_conditions = []
            for path in search_params['paths']:
                path_conditions.append("t.main_file LIKE ?")
                params.append(f'%{path}%')
            conditions.append(f"({' OR '.join(path_conditions)})")
        
        # 名称搜索（模糊匹配）
        if search_params.get('names'):
            name_conditions = []
            for name in search_params['names']:
                name_conditions.append("t.name LIKE ?")
                params.append(f'%{name}%')
            conditions.append(f"({' OR '.join(name_conditions)})")
        
        # 普通关键词（模糊搜索所有字段）
        if search_params.get('keywords'):
            keyword_conditions = []
            for keyword in search_params['keywords']:
                keyword_conditions.append(
                    "(t.name LIKE ? OR t.tag LIKE ? OR t.main_file LIKE ?)"
                )
                params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
            conditions.append(f"({' OR '.join(keyword_conditions)})")
        
        # 构建完整查询
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f'''
            SELECT 
                t.id as tuuid,
                t.name as tname,
                t.matchClass as tclass,
                t.main_file as tpath,
                t.icon_file as tpng,
                t.help_file as ttxt,
                t.tag as ttip,
                u.is_installed,
                u.is_favorite,
                u.usage_count
            FROM tools_index t
            INNER JOIN user_tools u ON t.id = u.tool_id
            WHERE {where_clause}
            ORDER BY u.is_favorite DESC, t.name
            LIMIT ? OFFSET ?
        '''
        
        params.extend([limit, offset])
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                'tuuid': row['tuuid'],
                'tname': row['tname'],
                'tclass': row['tclass'],
                'tpath': row['tpath'],
                'tpng': row['tpng'] if row['tpng'] else '',
                'ttxt': row['ttxt'] if row['ttxt'] else '',
                'ttip': row['ttip'] if row['ttip'] else '',
                'is_installed': row['is_installed'],
                'is_favorite': row['is_favorite'],
                'usage_count': row['usage_count']
            })
        
        return result
    
    def get_total_count(self, search_params, is_installed_only=False):
        """获取搜索结果总数"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        # 是否只搜索已安装的工具
        if is_installed_only:
            conditions.append("u.is_installed = 1")
        
        if search_params.get('classes'):
            class_conditions = []
            for cls in search_params['classes']:
                class_conditions.append("t.matchClass LIKE ?")
                params.append(f'%"{cls}"%')
            conditions.append(f"({' OR '.join(class_conditions)})")
        
        if search_params.get('labels'):
            label_conditions = []
            for label in search_params['labels']:
                label_conditions.append("t.tag LIKE ?")
                params.append(f'%{label}%')
            conditions.append(f"({' OR '.join(label_conditions)})")
        
        if search_params.get('paths'):
            path_conditions = []
            for path in search_params['paths']:
                path_conditions.append("t.main_file LIKE ?")
                params.append(f'%{path}%')
            conditions.append(f"({' OR '.join(path_conditions)})")
        
        if search_params.get('names'):
            name_conditions = []
            for name in search_params['names']:
                name_conditions.append("t.name LIKE ?")
                params.append(f'%{name}%')
            conditions.append(f"({' OR '.join(name_conditions)})")
        
        if search_params.get('keywords'):
            keyword_conditions = []
            for keyword in search_params['keywords']:
                keyword_conditions.append(
                    "(t.name LIKE ? OR t.tag LIKE ? OR t.main_file LIKE ?)"
                )
                params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
            conditions.append(f"({' OR '.join(keyword_conditions)})")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f'''
            SELECT COUNT(*) as count
            FROM tools_index t
            INNER JOIN user_tools u ON t.id = u.tool_id
            WHERE {where_clause}
        '''
        
        cursor.execute(query, params)
        return cursor.fetchone()['count']
    
    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None


class IconCache:
    """图标缓存管理器"""
    
    def __init__(self, toolbox_path):
        self._cache = {}
        self._base_path = toolbox_path
    
    def get_icon(self, icon_relative_path, size=QSize(20, 20)):
        if not icon_relative_path:
            return QIcon()
        
        if icon_relative_path in self._cache:
            return self._cache[icon_relative_path]
        
        full_path = os.path.join(self._base_path, icon_relative_path)
        
        if os.path.exists(full_path):
            pixmap = QPixmap(full_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                icon = QIcon(scaled_pixmap)
                self._cache[icon_relative_path] = icon
                return icon
        
        return QIcon()


class SmartCache:
    """智能缓存管理器"""
    
    def __init__(self, max_size=100):
        self._cache = {}  # {search_key: [tools]}
        self._max_size = max_size
        self._access_order = []  # 记录访问顺序（用于 LRU）
    
    def get(self, search_key):
        """获取缓存数据"""
        if search_key in self._cache:
            # 更新访问顺序
            if search_key in self._access_order:
                self._access_order.remove(search_key)
            self._access_order.append(search_key)
            return self._cache[search_key]
        return None
    
    def set(self, search_key, data):
        """设置缓存数据"""
        # 如果缓存满了，清理最久未使用的
        if len(self._cache) >= self._max_size and search_key not in self._cache:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]
        
        self._cache[search_key] = data
        
        # 更新访问顺序
        if search_key in self._access_order:
            self._access_order.remove(search_key)
        self._access_order.append(search_key)
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._access_order.clear()