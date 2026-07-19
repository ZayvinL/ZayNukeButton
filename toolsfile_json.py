# Copyright 2026 LIUXIAOBO (刘晓波)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import uuid
import paths_setup as psp
import JsonWriteRead as jwr


def get_all_files_fast(root_path):
    """高性能获取所有文件"""
    files = []
    for entry in os.scandir(root_path):
        # 如果路径中包含 # 号，则跳过（旧文件夹）
        if '#' in entry.path:
            continue
        if entry.is_file():
            files.append(entry.path)
        elif entry.is_dir():
            files.extend(get_all_files_fast(entry.path))
    return files


def generate_uuid():
    """生成唯一的 UUID"""
    return str(uuid.uuid4())


def get_relative_path(file_path, base_path):
    """
    获取相对于基准路径的相对路径，使用正斜杠保证跨平台兼容
    """
    rel_path = os.path.relpath(file_path, base_path)
    return rel_path.replace(os.sep, '/')


def scan_tool_files():
    """
    快速扫描所有工具文件及其配套文件
    
    Returns:
        list: 工具文件信息列表
    """
    tools_path = psp.tools_path_get()
    
    if not os.path.exists(tools_path):
        print(f"工具目录不存在: {tools_path}")
        return []
    
    # 获取所有文件（已自动排除 # 号文件夹）
    all_files = get_all_files_fast(tools_path)
    
    # 按工具主文件分组
    tool_groups = {}
    
    for file_path in all_files:
        filename = os.path.basename(file_path)
        dirname = os.path.dirname(file_path)
        
        # 跳过隐藏文件
        if filename.startswith('_'):
            continue
        
        # 识别工具主文件 (.py 或 .nk)
        if filename.endswith('.py') or filename.endswith('.nk'):
            tool_name = os.path.splitext(filename)[0]
            
            # 创建唯一标识
            rel_dir = get_relative_path(dirname, tools_path)
            tool_key = f"{rel_dir}/{tool_name}"
            
            if tool_key not in tool_groups:
                tool_groups[tool_key] = {
                    'main_file': None,
                    'json_file': None,
                    'html_file': None,
                    'icon_file': None,
                    'tool_name': tool_name,
                    'folder_rel': rel_dir
                }
            
            tool_groups[tool_key]['main_file'] = get_relative_path(file_path, tools_path)
            
        # 识别配套文件（只查找 .json、.png、.md）
        elif filename.endswith('.json'):
            base_name = filename.replace('.json', '')
            for key, group in tool_groups.items():
                if group['tool_name'] == base_name and group['folder_rel'] == get_relative_path(dirname, tools_path):
                    group['json_file'] = get_relative_path(file_path, tools_path)
                    break
                    
        elif filename.endswith('.png'):
            base_name = filename.replace('.png', '')
            for key, group in tool_groups.items():
                if group['tool_name'] == base_name and group['folder_rel'] == get_relative_path(dirname, tools_path):
                    group['icon_file'] = get_relative_path(file_path, tools_path)
                    break
                    
        elif filename.endswith(('.html', '.md', '.md')):
            base_name = filename.replace('.html', '').replace('.md', '').replace('.md', '')
            for key, group in tool_groups.items():
                if group['tool_name'] == base_name and group['folder_rel'] == get_relative_path(dirname, tools_path):
                    group['html_file'] = get_relative_path(file_path, tools_path)
                    break
        elif filename.endswith(('.md', '.markdown')):
            base_name = filename.replace('.md', '').replace('.markdown', '')
            for key, group in tool_groups.items():
                if group['tool_name'] == base_name and group['folder_rel'] == get_relative_path(dirname, tools_path):
                    group['html_file'] = get_relative_path(file_path, tools_path)
                    break
    
    # 转换为列表
    result = []
    for tool_key, group in tool_groups.items():
        if group['main_file']:
            result.append(group)
    
    return result


def ensure_tool_json(tool_info, tools_path):
    """
    确保工具存在 JSON 元数据文件，如果没有则创建
    
    JSON 格式统一为：工具名.json
    
    Returns:
        dict: 完整的元数据
    """
    tool_name = tool_info['tool_name']
    folder_rel = tool_info['folder_rel']
    
    # JSON 文件路径（统一使用简洁格式：工具名.json）
    json_rel = f"{folder_rel}/{tool_name}.json" if folder_rel else f"{tool_name}.json"
    json_abs = os.path.join(tools_path, json_rel.replace('/', os.sep))
    
    # 尝试加载已有的 JSON
    if os.path.exists(json_abs):
        metadata = jwr.ReadJson(json_abs)
        
        # 如果读取失败（返回空字典），创建新的
        if not metadata:
            metadata = create_new_metadata(tool_info)
            jwr.WriteJson(json_abs, metadata)
            return metadata
        
        # 确保有 UUID
        if 'id' not in metadata:
            metadata['id'] = generate_uuid()
        
        # 确保有 tag 字段
        if 'tag' not in metadata:
            metadata['tag'] = ''
        
        # 确保有 matchClass 字段（使用空列表）
        if 'matchClass' not in metadata:
            metadata['matchClass'] = []
        
        # 更新 files 字段，确保所有 key 都存在
        if 'files' not in metadata:
            metadata['files'] = {
                'main': tool_info['main_file'],
                'icon': tool_info['icon_file'],
                'help': tool_info['html_file']
            }
        else:
            # 补充缺失的 key
            if 'main' not in metadata['files']:
                metadata['files']['main'] = tool_info['main_file']
            if 'icon' not in metadata['files']:
                metadata['files']['icon'] = tool_info['icon_file']
            if 'help' not in metadata['files']:
                metadata['files']['help'] = tool_info['html_file']
        
        # 保存更新后的元数据
        jwr.WriteJson(json_abs, metadata)
        return metadata
    
    # 创建新的元数据
    metadata = create_new_metadata(tool_info)
    jwr.WriteJson(json_abs, metadata)
    
    return metadata


def create_new_metadata(tool_info):
    """
    创建新的工具元数据
    
    Args:
        tool_info: 工具文件信息
    
    Returns:
        dict: 新元数据字典
    """
    return {
        'id': generate_uuid(),
        'name': tool_info['tool_name'],
        'tag': '',
        'matchClass': [],
        'files': {
            'main': tool_info['main_file'],
            'icon': tool_info['icon_file'],
            'help': tool_info['html_file']
        }
    }


def get_all_tools():
    """
    获取所有工具的完整信息
    
    Returns:
        list: 工具元数据列表
    """
    tools_path = psp.tools_path_get()
    
    if not os.path.exists(tools_path):
        print(f"工具目录不存在: {tools_path}")
        return []
    
    # 扫描所有工具文件（已排除 # 号文件夹）
    tool_files = scan_tool_files()
    
    # 为每个工具确保有 JSON 元数据
    tools_data = []
    for tool_info in tool_files:
        metadata = ensure_tool_json(tool_info, tools_path)
        metadata['_tools_root'] = tools_path
        tools_data.append(metadata)
    
    return tools_data


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("测试工具扫描功能")
    print("=" * 60)
    
    tools = get_all_tools()
    print(f"\n共找到 {len(tools)} 个工具\n")
    
    for i, tool in enumerate(tools[:3], 1):
        print(f"工具 {i}:")
        print(f"  ID: {tool.get('id', 'N/A')}")
        print(f"  名称: {tool.get('name', 'N/A')}")
        print(f"  标签: {tool.get('tag', 'N/A')}")
        print(f"  匹配类: {tool.get('matchClass', 'N/A')}")
        print(f"  文件: {tool.get('files', {})}")
        print()