# -*- coding: utf-8 -*-
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

import nuke
import nukescripts
import getpass
import os
import sys
import shutil
import JsonWriteRead as RWJ
import QuanXianSet as quanxian
import uuid
import paths_setup as psp

import sqlite3
import sqlite_file_setup as sfs
import json

# 写py文件
def WritePyFile(path,strcm=""):
    Writedata = strcm
    with open(path, "w", encoding='utf-8') as f:
        f.write(Writedata)

# 写py文件2
def WritePyFilepy2(path,strcm=""):
    Writedata = strcm   
    path=unicode(path,'utf-8')
    with open(path, "w") as f:
        f.write(Writedata)


# 生成json文件
def GenerateJsonFile(tool_name, main_file, icon_file=None, help_file=None, tag="", matchClass=None):
    """
    生成工具的 JSON 配置文件
    
    参数:
        tool_name: 工具名称
        main_file: 主脚本文件路径或名称
        icon_file: 图标文件路径（可选）
        help_file: 帮助文件路径（可选）
        tag: 工具标签（可选）
        matchClass: 匹配的节点类列表（可选）
    
    返回:
        生成的 JSON 文件路径
    """
   
    
    # 生成唯一 ID
    tool_id = str(uuid.uuid4())
    
    # 构建 files 字典
    files_dict = {
        "help": help_file,
        "icon": icon_file,
        "main": main_file
    }
    
    # 如果 matchClass 为 None，则使用空列表
    if matchClass is None:
        matchClass = []
    else:
        # 按逗号分割并去除空白
        matchClass = [item.strip() for item in matchClass.split(',') if item.strip()]
    
    # 构建完整的 JSON 数据结构
    json_data = {
        "files": files_dict,
        "id": tool_id,
        "matchClass": matchClass,
        "name": tool_name,
        "tag": tag
    }
    
    # 生成 JSON 文件名（与主脚本文件同名，但扩展名为 .json）
    if main_file.endswith('.py'):
        json_filename = main_file[:-3] + '.json'
    elif main_file.endswith('.nk'):
        json_filename = main_file[:-3] + '.json'
    else:
        json_filename = main_file + '.json'
    
    # 获取 tools 目录路径
    tools_path = psp.tools_path_get()
    json_filepath = os.path.join(tools_path, json_filename)
    
    # 使用 JsonWriteRead 模块写入 JSON 文件
    RWJ.WriteJson(json_filepath, json_data)
    
    print(f"✓ JSON 文件已生成: {json_filepath}")
    print(f"  工具 ID: {tool_id}")
    print(f"  工具名称: {tool_name}")
    
    return json_filepath


# 生成数据库记录
def AddToolToDatabase(tool_id, tool_name, main_file, icon_file=None, help_file=None, tag="", matchClass=None, db_path=None):
    """
    将工具信息添加到数据库
    
    参数:
        tool_id: 工具唯一 ID
        tool_name: 工具名称
        main_file: 主脚本文件路径
        icon_file: 图标文件路径（可选）
        help_file: 帮助文件路径（可选）
        tag: 工具标签（可选）
        matchClass: 匹配的节点类列表（可选）
        db_path: 数据库路径（可选，默认使用当前用户数据库）
    
    返回:
        是否成功添加
    """

    
    # 如果未指定数据库路径，则使用当前用户的数据库
    if db_path is None:
        db_path = sfs.get_user_db_path()
    
    # 初始化数据库（如果尚未初始化）
    sfs.init_database(db_path)
    
    # 处理 matchClass
    if matchClass is None:
        matchClass = []
    else:
        # 按逗号分割并去除空白
        matchClass = [item.strip() for item in matchClass.split(',') if item.strip()]
    matchClass_json = json.dumps(matchClass, ensure_ascii=False)
    
    # 提取分类信息（从文件路径中）
    category = ''
    if main_file:
        parts = main_file.split('/')
        if len(parts) > 1:
            category = '/'.join(parts[:-1])
    
    # 判断是否有图标和帮助文件
    has_icon = 1 if icon_file else 0
    has_help = 1 if help_file else 0
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 插入工具索引记录
        cursor.execute('''
            INSERT OR REPLACE INTO tools_index (
                id, name, tag, matchClass, main_file, 
                icon_file, help_file, category, has_icon, has_help
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (tool_id, tool_name, tag, matchClass_json, main_file, 
              icon_file, help_file, category, has_icon, has_help))
        
        # 插入用户工具记录（默认安装、未收藏）
        cursor.execute('''
            INSERT OR IGNORE INTO user_tools (tool_id, is_installed) VALUES (?, 1)
        ''', (tool_id,))
        
        conn.commit()
        print(f"✓ 工具已成功添加到数据库")
        print(f"  工具 ID: {tool_id}")
        print(f"  工具名称: {tool_name}")
        return True
        
    except Exception as e:
        print(f"✗ 添加工具到数据库时出错: {str(e)}")
        conn.rollback()
        return False
        
    finally:
        conn.close()





class ExportToolPanel( nukescripts.PythonPanel ):
    def __init__( self, node=None ):
        nukescripts.PythonPanel.__init__( self, '导出工具' )
        # ------------------------
        username = getpass.getuser()
        pt = psp.tools_path_get()    
        # 确保输出文件夹存在
        os.makedirs(pt, exist_ok=True)
        csspt = f'{pt}/01-USER/{username}/'
        self.ptc = f'01-USER/{username}/'
        if not os.path.exists(csspt):
            os.makedirs(csspt)
        # ------------------------
        self.curpath = csspt
        # ----------------------
        self.buta = nuke.PyScript_Knob("Pubta","Nuke工具")
        self.buta.setFlag( nuke.STARTLINE )
        self.butb = nuke.PyScript_Knob("Pubtb","Python工具")
        self.butd = nuke.PyScript_Knob("Pubtd","添加类")
        self.bute = nuke.PyScript_Knob("Pubte","说明")

        sds = nuke.selectedNodes()
        glssv = [i.Class() for i in sds]
        gvs = []
        for i in glssv:
            if i not in gvs:
                gvs.append(i)
            

        clsslist = ["None","AnyTime","NoSelectedNode","AnySelectedNode"]+gvs
        
        self.typelista = nuke.Enumeration_Knob("typea","类：",clsslist)
        
        self.name = nuke.String_Knob("name","名字","")
        #self.note = nuke.String_Knob("note","备注","")
        self.tipv = nuke.String_Knob("tip","tip","")
        self.classlist = nuke.String_Knob("classlist","适用类","")
        
        self.daima = nuke.Multiline_Eval_String_Knob("daimawrite","代码","")
        
        
        #self.resize(800,800)

        # ADD KOBS ,self.note
        for k in ( self.name,self.tipv,self.classlist,
                    self.typelista,self.butd,self.bute,
                    self.daima,
                    self.buta,self.butb
                ):
                
            self.addKnob( k )
            
    def knobChanged( self, knob ):
        if knob == self.butd:
            self.addclassname()
        if knob == self.buta:
            self.expnuke()
        if knob == self.butb:
            self.exppython()
        if knob == self.name:
            pass
        # if knob == self.note:
        #     pass
        if knob == self.typelista:
            pass
        if knob == self.daima:
            pass
        if knob == self.bute:
            nuke.message("CBA-按钮展示，任何有选中节点时展示这个工具；\nCBB-按钮展示，没有选中节点时展示这个工具")
        
    def exprot_tool(self,type="Python"):
        curpn = self.name.value()
        # note = self.note.value()
        ttip = self.tipv.value()
        
        if curpn.strip() == "":
            print("请设置工具名称")
            return 
        # if note.strip() == "":
        #     note = "note"

        if ttip.strip() == "":
            ttip = ""
        tool_name = curpn.strip()
        
        if type == "Nuke":
            n_toolname = tool_name + '.nk'
        elif type == "Python":
            n_toolname = tool_name + '.py' 
        else:
            print("导出格式错误")
            return 
        classname = self.classlist.value()
        if classname == "":
            classname = "None"

        matchClass = classname
        
        path = self.curpath + n_toolname  
        main_filename = self.ptc + n_toolname
        icon_file = None
        help_file = None
        tag = ttip
        dirname, filename = os.path.split(path)
        # ---------------------------------------
        if type == "Nuke":
            tempexport = psp.tempexportpath_get()
            temp_name = tempexport + "TEMPNAME.nk"
            nuke.nodeCopy(temp_name)
            shutil.move(temp_name, path)
            
            
        elif type == "Python":
            # 写入代码到文件
            pythonScript = self.daima.value()
            if nuke.NUKE_VERSION_MAJOR < 13:
                WritePyFilepy2(path,pythonScript)
            else:
                WritePyFile(path,pythonScript) 
        
        # 尝试为导出文件设置共享权限
        perm_ok1 = quanxian.set_file_permissions(path)

        # 生成 JSON 文件
        json_filepath = GenerateJsonFile(
            tool_name=tool_name,
            main_file=main_filename,
            icon_file=icon_file,
            help_file=help_file,
            tag=tag,
            matchClass=matchClass
        )

        # 读取生成的 JSON 文件获取 tool_id
        json_data = RWJ.ReadJson(json_filepath)
        # 尝试为JSON文件设置共享权限
        perm_ok2 = quanxian.set_file_permissions(json_filepath)

        # 如果单文件权限设置失败，提示一次性目录配置方案
        if not (perm_ok1 and perm_ok2):
            tools_dir = psp.tools_path_get()
            print("=" * 55)
            print("[提示] 文件权限设置未完全成功，多用户共享可能受限。")
            print("  请管理员执行以下一次性配置（仅需一次）：")
            print("  import QuanXianSet")
            print('  QuanXianSet.setup_directory_shared_permissions("{}")'.format(tools_dir))
            print("=" * 55)

        tool_id = json_data.get('id')
        
        # 添加到数据库
        if tool_id:
            AddToolToDatabase(
                tool_id=tool_id,
                tool_name=tool_name,
                main_file=main_filename,  # 数据库中保存相对路径
                icon_file=icon_file,
                help_file=help_file,
                tag=tag,
                matchClass=matchClass
            )
        
        
        self.finishModalDialog("done")
    
    def exppython(self):
        self.exprot_tool("Python")
    
    def expnuke(self):   
        self.exprot_tool("Nuke")
        
    
    def addclassname(self):
        curlei = self.typelista.value()
        leilist = self.classlist.value().split(",")
        clist = [i for i in leilist if i != ""]
        if curlei not in clist:
            clist.append(curlei)
            zc = ",".join(clist)
            self.classlist.setValue(zc)
        
            



def run_show():
    pnshw = ExportToolPanel()
    pnshw.setMinimumSize(800,500)
    pnshw.showModal()



