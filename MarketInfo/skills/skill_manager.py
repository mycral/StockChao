# -*- coding: utf-8 -*-
"""
选股技能管理器
负责技能的注册、加载、列表、删除等操作
"""
import os
import sys
import json
import importlib
import inspect
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from skills.skill_base import BaseSkill, SkillMeta, Condition, get_skill_info
from config import DB_PATH


class SkillManager:
    """选股技能管理器"""

    def __init__(self, skills_dir=None, config_file=None):
        """
        Args:
            skills_dir: 技能目录路径
            config_file: 技能配置文件路径
        """
        parent_dir = os.path.dirname(DB_PATH)
        self.skills_dir = skills_dir or os.path.join(parent_dir, 'skills')
        self.config_file = config_file or os.path.join(parent_dir, 'skills.json')
        self.skills = {}  # {skill_name: skill_module}

    def _ensure_skills_dir(self):
        """确保技能目录存在"""
        os.makedirs(self.skills_dir, exist_ok=True)
        # 确保 __init__.py 存在
        init_file = os.path.join(self.skills_dir, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('# -*- coding: utf-8 -*-\n')
                f.write('# Skills package\n')

    def load_skills(self):
        """加载所有技能"""
        self.skills = {}

        if not os.path.exists(self.skills_dir):
            self._ensure_skills_dir()
            return

        for filename in os.listdir(self.skills_dir):
            # 只加载 _skill.py 结尾的文件
            if not filename.endswith('_skill.py'):
                continue
            if filename.startswith('__'):
                continue

            module_name = filename[:-3]
            try:
                # 动态导入模块
                module = importlib.import_module(f'skills.{module_name}')

                # 获取技能信息
                info = get_skill_info(module)
                meta = info['meta']
                skill_name = meta.name

                self.skills[skill_name] = {
                    'meta': meta,
                    'conditions': info['conditions'],
                    'module': module,
                    'filename': filename,
                }

                print(f"加载技能: {skill_name} (v{meta.version})")

            except Exception as e:
                print(f"加载技能 {filename} 失败: {e}")

    def get_skills_list(self):
        """获取技能列表"""
        result = []
        for name, info in self.skills.items():
            result.append({
                'name': name,
                'meta': info['meta'].to_dict(),
                'conditions': [c.to_dict() if isinstance(c, Condition) else c for c in info['conditions']],
                'filename': info['filename'],
            })
        return result

    def get_skill(self, name):
        """获取技能实例"""
        if name not in self.skills:
            return None

        info = self.skills[name]
        module = info['module']

        # 获取模块中的 Skill 类
        for item_name, item in inspect.getmembers(module):
            if inspect.isclass(item) and issubclass(item, BaseSkill) and item is not BaseSkill:
                # 使用配置中的 DB_PATH
                from config import DB_PATH
                return item(db_path=DB_PATH)

        return None

    def run_skill(self, name, conditions=None, save_result=True):
        """运行技能"""
        skill = self.get_skill(name)
        if skill is None:
            print(f"技能不存在: {name}")
            return None

        return skill.run(conditions=conditions, save_result=save_result)

    def create_skill(self, name, description, conditions=None, author=''):
        """创建新技能"""
        self._ensure_skills_dir()

        # 生成安全的文件名
        safe_name = name.replace(' ', '_').replace('/', '_')
        filename = f"{safe_name}_skill.py"
        filepath = os.path.join(self.skills_dir, filename)

        if os.path.exists(filepath):
            print(f"技能文件已存在: {filename}")
            return False

        # 生成条件代码
        conditions_code = ''
        if conditions:
            cond_lines = []
            for cond in conditions:
                if isinstance(cond, dict):
                    cond_lines.append(f"    Condition(name='{cond['name']}', label='{cond['label']}', type='{cond.get('type', 'string')}', default={cond.get('default')}),")
            conditions_code = '\n'.join(cond_lines)

        # 生成技能代码
        template = f'''# -*- coding: utf-8 -*-
"""
{name} 选股技能
{description}
"""
import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from skills.skill_base import BaseSkill, SkillMeta, Condition
from config import DB_PATH


meta = SkillMeta(
    name='{name}',
    description='{description}',
    version='1.0',
    author='{author}',
    tags=[],
)

conditions = [
{conditions_code}
]


class Skill(BaseSkill):
    """具体选股实现"""

    def screen(self, conditions=None):
        """执行选股"""
        if conditions is None:
            conditions = self.get_default_conditions()

        # TODO: 实现选股逻辑
        conn = sqlite3.connect(self.db_path)
        # 示例：获取所有股票
        sql = """
            SELECT b.ts_code, b.name
            FROM stock_basic b
            LIMIT 10
        """
        result = pd.read_sql_query(sql, conn)
        conn.close()

        return result


if __name__ == '__main__':
    skill = Skill()
    print(f"执行技能: {{skill.get_meta().name}}")
    result = skill.run()
    if result is not None and len(result) > 0:
        print(f"找到 {{len(result)}} 只股票")
        print(result.head())
'''

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(template)

        print(f"已创建技能: {name}")
        print(f"文件: {filepath}")
        print("请编辑文件实现具体的选股逻辑")

        return True

    def delete_skill(self, name):
        """删除技能"""
        if name not in self.skills:
            print(f"技能不存在: {name}")
            return False

        info = self.skills[name]
        filepath = os.path.join(self.skills_dir, info['filename'])

        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"已删除技能: {name}")
            del self.skills[name]
            return True

        return False

    def save_skills_config(self):
        """保存技能配置到文件"""
        config = {
            'updated_at': datetime.now().strftime('%Y%m%d %H:%M:%S'),
            'skills': self.get_skills_list(),
        }

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(f"技能配置已保存: {self.config_file}")

    def load_skills_config(self):
        """从文件加载技能配置"""
        if not os.path.exists(self.config_file):
            return {}

        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def print_skills(self):
        """打印技能列表"""
        if not self.skills:
            print("暂无技能")
            return

        print(f"\n{'='*60}")
        print(f"选股技能列表 (共 {len(self.skills)} 个)")
        print(f"{'='*60}")

        for name, info in self.skills.items():
            meta = info['meta']
            conditions = info['conditions']
            print(f"\n【{meta.name}】 v{meta.version}")
            print(f"  描述: {meta.description}")
            print(f"  作者: {meta.author}")
            print(f"  标签: {', '.join(meta.tags) or '无'}")
            print(f"  条件: {len(conditions)} 个")
            for cond in conditions:
                if isinstance(cond, Condition):
                    print(f"    - {cond.label} ({cond.name}): {cond.default}")


# ==================== 命令行接口 ====================
def main():
    import argparse

    parser = argparse.ArgumentParser(description='选股技能管理')
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # list 命令
    subparsers.add_parser('list', help='列出所有技能')

    # run 命令
    run_parser = subparsers.add_parser('run', help='运行技能')
    run_parser.add_argument('name', help='技能名称')
    run_parser.add_argument('--save', action='store_true', default=True, help='保存结果')
    run_parser.add_argument('--condition', '-c', action='append', help='条件，如 -c key=value')

    # create 命令
    create_parser = subparsers.add_parser('create', help='创建新技能')
    create_parser.add_argument('name', help='技能名称')
    create_parser.add_argument('--desc', '-d', default='', help='技能描述')
    create_parser.add_argument('--author', '-a', default='', help='作者')

    args = parser.parse_args()

    manager = SkillManager()
    manager.load_skills()

    if args.command == 'list':
        manager.print_skills()

    elif args.command == 'run':
        conditions = {}
        if args.condition:
            for c in args.condition:
                if '=' in c:
                    key, value = c.split('=', 1)
                    # 尝试转换类型
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                    conditions[key] = value

        result = manager.run_skill(args.name, conditions=conditions, save_result=args.save)
        if result is not None and len(result) > 0:
            print(f"\n选股结果 ({len(result)} 只):")
            print(result.head(20))

    elif args.command == 'create':
        manager.create_skill(args.name, args.desc, author=args.author)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
