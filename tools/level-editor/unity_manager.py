# unity_manager.py
import os
import json
import ntpath
import UnityPy

class UnityABManager:
    """负责处理与 Unity AssetBundle 相关的读写和重新打包操作"""
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.base_dir, "data")
        self.out_dir = os.path.join(self.base_dir, "out")
        self.level_to_file_map = {} # maps level_id -> (number, filename, file_path)
        self._cached_level_ids = None # Cache for scanned level IDs

    def check_input_exists(self):
        """检查是否存在以 data_assets 开头的数据文件"""
        if not os.path.exists(self.data_dir):
            return False
        for filename in os.listdir(self.data_dir):
            if filename.startswith("data_assets"):
                return True
        return False

    def _get_sorted_data_files(self):
        """获取所有符合条件的 data_assets 文件，并按数字从大到小排序"""
        if not os.path.exists(self.data_dir):
            return []
        
        import re
        files = []
        for filename in os.listdir(self.data_dir):
            if filename.startswith("data_assets"):
                digits = re.findall(r"\d+", filename)
                if digits:
                    num = int(digits[-1])
                    full_path = os.path.join(self.data_dir, filename)
                    files.append((num, filename, full_path))
        
        if not files:
            return []
            
        numbers = [item[0] for item in files]
        if len(files) > 1:
            if len(set(numbers)) == 1:
                raise ValueError("检测到多个数据文件，但它们的数字都一样，无法区分优先级！")
            if len(set(numbers)) < len(numbers):
                raise ValueError("检测到重复的数字，无法区分优先级！")
                
        # 按数字从大到小排序
        files.sort(key=lambda x: x[0], reverse=True)
        return files

    # ------------------ 终极类型嗅探兼容方法 ------------------
    def _get_name(self, data_obj):
        """智能提取对象名称 (兼容各种 UnityPy 映射缺失)"""
        # 1. 尝试常规语法糖
        if hasattr(data_obj, 'name') and data_obj.name:
            return data_obj.name
        # 2. 尝试底层字段 (如你 dump 出来的 m_Name)
        if hasattr(data_obj, 'm_Name') and data_obj.m_Name:
            return data_obj.m_Name
        # 3. 兜底方案：从容器路径中截取文件名
        if hasattr(data_obj, 'container') and data_obj.container:
            filename = ntpath.basename(data_obj.container)
            return filename.split('.')[0]
        return "Unknown_TextAsset"

    def _get_text(self, data_obj):
        """智能判断并提取 TextAsset 内容 (兼容 m_Script)"""
        for attr in ['text', 'script', 'm_Script']:
            if hasattr(data_obj, attr):
                val = getattr(data_obj, attr)
                if isinstance(val, str):
                    return val
                if isinstance(val, (bytes, bytearray)):
                    return bytes(val).decode('utf-8', errors='ignore')
        return ""

    def _set_text(self, data_obj, new_text):
        """写入时保持与原始数据类型一致"""
        new_bytes = new_text.encode('utf-8')
        for attr in ['text', 'script', 'm_Script']:
            if hasattr(data_obj, attr):
                original_val = getattr(data_obj, attr)
                if isinstance(original_val, str):
                    setattr(data_obj, attr, new_text)
                else:
                    setattr(data_obj, attr, new_bytes)
        data_obj.save()
    # ----------------------------------------------------------

    def get_all_level_ids(self, force_refresh=False):
        """遍历所有 AB 包，返回所有关卡配置的 TextAsset 名称"""
        if not force_refresh and self._cached_level_ids is not None:
            return self._cached_level_ids

        files = self._get_sorted_data_files()
        if not files:
            return []
        
        self.level_to_file_map = {}
        all_level_ids = set()
        
        for num, filename, file_path in files:
            try:
                env = UnityPy.load(file_path)
                for obj in env.objects:
                    if obj.type.name == "TextAsset":
                        data = obj.read()
                        text_content = self._get_text(data)
                        
                        # 过滤出包含关卡特征的文本
                        if text_content and '"PlayerConfig"' in text_content and '"BoardConfig"' in text_content:
                            level_name = self._get_name(data)
                            # 因为是数字从大到小排序，如果同一个关卡 ID 存在于多个包中，
                            # 我们只保留数字大的那个，所以如果已经有了就跳过，这样实现“数字大的先读”且唯一
                            if level_name not in self.level_to_file_map:
                                self.level_to_file_map[level_name] = (num, filename, file_path)
                                all_level_ids.add(level_name)
            except Exception as e:
                raise ValueError(f"读取数据文件 {filename} 失败: {str(e)}")
                
        self._cached_level_ids = sorted(list(all_level_ids))
        return self._cached_level_ids

    def load_level(self, level_id):
        """从 AB 包提取指定关卡的 JSON 字典"""
        if not self.level_to_file_map or level_id not in self.level_to_file_map:
            self.get_all_level_ids()
            
        if level_id not in self.level_to_file_map:
            raise ValueError(f"在所有 AB 包中均未找到关卡: {level_id}")
            
        num, filename, file_path = self.level_to_file_map[level_id]
        
        env = UnityPy.load(file_path)
        for obj in env.objects:
            if obj.type.name == "TextAsset":
                data = obj.read()
                if self._get_name(data) == level_id:
                    text_content = self._get_text(data)
                    try:
                        return json.loads(text_content)
                    except Exception as e:
                        raise ValueError(f"解析 JSON 失败 ({level_id}) 来自 {filename}: {str(e)}\n\n截取的文本开头:\n{text_content[:200]}")
        
        raise ValueError(f"在文件 {filename} 中未找到关卡: {level_id}")

    def pack_level(self, level_id, config_dict):
        """将修改后的字典转为 JSON 文本，覆盖回 AB 包并导出到 out 目录"""
        if not self.level_to_file_map or level_id not in self.level_to_file_map:
            self.get_all_level_ids()
            
        if level_id not in self.level_to_file_map:
            raise ValueError(f"在任何底包中均未找到对应的关卡 '{level_id}'！")
            
        num, filename, file_path = self.level_to_file_map[level_id]
        
        env = UnityPy.load(file_path)
        found = False
        
        for obj in env.objects:
            if obj.type.name == "TextAsset":
                data = obj.read()
                if self._get_name(data) == level_id:
                    new_text = json.dumps(config_dict, indent=4, ensure_ascii=False)
                    self._set_text(data, new_text)
                    found = True
                    break
        
        if not found:
            raise ValueError(f"未在底包文件 '{filename}' 中找到关卡 '{level_id}'！")
        
        output_ab_path = os.path.join(self.out_dir, filename)
        os.makedirs(os.path.dirname(output_ab_path), exist_ok=True)
        
        with open(output_ab_path, "wb") as f:
            f.write(env.file.save())
            
        return output_ab_path