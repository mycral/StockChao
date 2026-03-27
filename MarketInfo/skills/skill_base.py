# -*- coding: utf-8 -*-
"""
选股技能基类
所有选股技能都需要继承这个基类
"""
import os
import sys
import inspect
import pandas as pd
from datetime import datetime

# 添加父目录到路径，以便导入 config
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class SkillMeta:
    """技能元信息"""

    def __init__(self, name, description, version='1.0', author='', tags=None):
        self.name = name
        self.description = description
        self.version = version
        self.author = author or os.environ.get('USER', 'unknown')
        self.created_date = datetime.now().strftime('%Y%m%d')
        self.tags = tags or []

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'created_date': self.created_date,
            'tags': self.tags,
        }


class Condition:
    """选股条件"""

    def __init__(self, name, label, type='string', default=None, options=None):
        """
        Args:
            name: 条件名称（用于代码引用）
            label: 条件显示标签
            type: 类型 (string/number/percent/select/date)
            default: 默认值
            options: 下拉选项列表 [{"label": "xxx", "value": "xxx"}]
        """
        self.name = name
        self.label = label
        self.type = type
        self.default = default
        self.options = options

    def to_dict(self):
        return {
            'name': self.name,
            'label': self.label,
            'type': self.type,
            'default': self.default,
            'options': self.options,
        }


class BaseSkill:
    """选股技能基类"""

    # 子类需要定义这些属性
    meta = None  # SkillMeta 对象
    conditions = []  # 条件列表 [Condition(...), ...]

    def __init__(self, db_path=None):
        from config import DB_PATH
        self.db_path = db_path or DB_PATH

    def get_meta(self):
        """获取技能元信息"""
        # 检查实例属性
        if self.meta is not None:
            if isinstance(self.meta, dict):
                self.meta = SkillMeta(**self.meta)
            return self.meta

        # 检查类属性
        if hasattr(self.__class__, 'meta') and self.__class__.meta is not None:
            self.meta = self.__class__.meta
            if isinstance(self.meta, dict):
                self.meta = SkillMeta(**self.meta)
            return self.meta

        # 从模块中查找
        module = sys.modules.get(self.__class__.__module__)
        if module and hasattr(module, 'meta'):
            self.meta = module.meta
            if isinstance(self.meta, dict):
                self.meta = SkillMeta(**self.meta)
            return self.meta

        raise NotImplementedError("子类必须定义 meta 属性")

    def get_conditions(self):
        """获取选股条件列表"""
        if self.conditions:
            return self.conditions

        # 检查类属性
        if hasattr(self.__class__, 'conditions') and self.__class__.conditions:
            self.conditions = self.__class__.conditions
            return self.conditions

        # 从模块中查找
        module = sys.modules.get(self.__class__.__module__)
        if module and hasattr(module, 'conditions'):
            self.conditions = module.conditions
            return self.conditions

        return []

    def get_default_conditions(self):
        """获取默认条件值"""
        defaults = {}
        for cond in self.get_conditions():
            defaults[cond.name] = cond.default
        return defaults

    def screen(self, conditions=None):
        """
        执行选股逻辑

        Args:
            conditions: 条件参数字典，如果为 None 则使用默认值

        Returns:
            DataFrame: 选股结果，必须包含 ts_code 和 name 列
        """
        raise NotImplementedError("子类必须实现 screen 方法")

    def run(self, conditions=None, save_result=True):
        """
        运行技能

        Args:
            conditions: 条件参数字典
            save_result: 是否保存结果

        Returns:
            DataFrame: 选股结果
        """
        if conditions is None:
            conditions = self.get_default_conditions()

        result = self.screen(conditions)

        if save_result and result is not None and len(result) > 0:
            self.save_result(result)

        return result

    def save_result(self, result, filename=None):
        """保存选股结果"""
        from config import DB_PATH as parent_db_path
        results_dir = os.path.join(os.path.dirname(parent_db_path), 'skill_results')
        os.makedirs(results_dir, exist_ok=True)

        if filename is None:
            meta = self.get_meta()
            safe_name = meta.name.replace(' ', '_').replace('/', '_')
            filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = os.path.join(results_dir, filename)
        result.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"结果已保存: {filepath}")
        return filepath


def get_skill_info(skill_module):
    """从模块获取技能信息"""
    # 获取 meta 属性
    if hasattr(skill_module, 'meta'):
        meta = skill_module.meta
        if isinstance(meta, dict):
            meta = SkillMeta(**meta)
    elif hasattr(skill_module, 'SkillMeta'):
        meta = skill_module.SkillMeta(
            name=skill_module.__name__,
            description=getattr(skill_module, '__doc__', '') or ''
        )
    else:
        meta = SkillMeta(
            name=skill_module.__name__,
            description=getattr(skill_module, '__doc__', '') or ''
        )

    # 获取 conditions
    conditions = []
    if hasattr(skill_module, 'conditions'):
        for cond in skill_module.conditions:
            if isinstance(cond, dict):
                cond = Condition(**cond)
            conditions.append(cond)

    return {
        'meta': meta,
        'conditions': conditions,
    }
