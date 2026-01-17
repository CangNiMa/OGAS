#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
维多利亚3建筑生产方法物资关系表格生成程序
用于分析建筑、生产方法组、生产方法与物资之间的关系
"""

import os
import re
from typing import List, Dict, Set, Tuple

class Victoria3DataAnalyzer:
    def __init__(self, base_path: str = "."):
        self.base_path = base_path
        self.goods_list = []
        self.buildings_hierarchy = []  # 存储建筑→生产方法组→生产方法的层级关系
        self.production_method_groups_data = {}  # 存储生产方法组数据
        self.production_method_groups_texture = {}  # 存储生产方法组的texture信息
        self.goods_relations = {}  # 存储生产方法的物资关系
        
    def extract_goods_names(self) -> List[str]:
        """从goods/00_goods.txt中提取所有物资名"""
        goods_file = os.path.join(self.base_path, "goods", "00_goods.txt")
        goods_names = []
        
        try:
            with open(goods_file, 'r', encoding='utf-8') as f:
                content = f.read()

                # 处理BOM字符：移除文件开头的BOM字符
                if content.startswith('\ufeff'):
                    content = content[1:]
                    
                # 匹配物资名定义模式：物资名 = {
                pattern = r'^\w+'
                matches = re.findall(pattern, content, re.MULTILINE)
                goods_names = matches
        except FileNotFoundError:
            print(f"错误：找不到文件 {goods_file}")
        except Exception as e:
            print(f"读取物资文件时出错：{e}")
            
        return goods_names
    
    def extract_buildings_hierarchy(self):
        """提取建筑→生产方法组→生产方法的层级关系"""
        buildings_dir = os.path.join(self.base_path, "buildings")
        pmg_dir = os.path.join(self.base_path, "production_method_groups")
        
        # 首先加载所有生产方法组数据
        self._load_production_method_groups(pmg_dir)
        
        # 存储建筑的required_construction值
        self.building_construction_costs = {}
        
        # 按buildings文件夹内文件顺序处理建筑
        try:
            building_files = sorted([f for f in os.listdir(buildings_dir) 
                                   if f.endswith('.txt') and not f.startswith('.')])
            
            for filename in building_files:
                filepath = os.path.join(buildings_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                    # 处理BOM字符：移除文件开头的BOM字符
                    if content.startswith('\ufeff'):
                        content = content[1:]
                    
                    # 使用更精确的正则表达式匹配建筑定义（处理嵌套大括号）
                    building_pattern = r'^(\w+)\s*=\s*\{([\s\S]*?)^\}$'
                    building_matches = re.findall(building_pattern, content, re.MULTILINE)
                    
                    for building_name, building_content in building_matches:
                        # 提取建筑的required_construction值
                        construction_pattern = r'required_construction\s*=\s*(\w+)'
                        construction_match = re.search(construction_pattern, building_content)
                        construction_cost = ""
                        if construction_match:
                            construction_cost = construction_match.group(1)
                        
                        # 存储建筑的construction cost
                        self.building_construction_costs[building_name] = construction_cost
                        
                        # 提取建筑的生产方法组
                        pmg_pattern = r'production_method_groups\s*=\s*\{([^}]*)\}'
                        pmg_match = re.search(pmg_pattern, building_content, re.DOTALL)
                        
                        if pmg_match:
                            pmg_content = pmg_match.group(1)
                            # 提取生产方法组名（按定义顺序，使用更精确的匹配）
                            pmg_names = re.findall(r'(\w+)', pmg_content)
                            pmg_names = [name for name in pmg_names if name]  # 过滤空名
                            
                            # 为每个生产方法组添加其生产方法
                            for pmg_name in pmg_names:
                                if pmg_name in self.production_method_groups_data:
                                    production_methods = self.production_method_groups_data[pmg_name]
                                    self.buildings_hierarchy.append({
                                        'building': building_name,
                                        'production_method_group': pmg_name,
                                        'production_methods': production_methods
                                    })
        except Exception as e:
            print(f"提取建筑层级关系时出错：{e}")
    
    def _classify_pmg_type(self, pmg_content: str) -> str:
        """根据pmg_content中的关键字进行分类"""
        if 'mixed_icon_base' in pmg_content:
            return 'base'
        elif 'mixed_icon_refining' in pmg_content:
            return 'refining'
        elif 'mixed_icon_automation' in pmg_content:
            return 'automation'
        elif 'mixed_icon_military' in pmg_content:
            return 'military'
        elif 'mixed_icon_ownership' in pmg_content:
            return 'ownership'
        else:
            return 'other'
    
    def _load_production_method_groups(self, pmg_dir: str):
        """加载所有生产方法组数据"""
        try:
            for filename in os.listdir(pmg_dir):
                if filename.endswith('.txt') and not filename.startswith('.'):
                    filepath = os.path.join(pmg_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                        # 处理BOM字符：移除文件开头的BOM字符
                        if content.startswith('\ufeff'):
                            content = content[1:]
                        
                        # 使用更精确的正则表达式匹配生产方法组定义
                        pmg_pattern = r'^(\w+)\s*=\s*\{([\s\S]*?)^\}$'
                        pmg_matches = re.findall(pmg_pattern, content, re.MULTILINE)
                        
                        for pmg_name, pmg_content in pmg_matches:
                            # 根据pmg_content中的关键字进行分类
                            pmg_type = self._classify_pmg_type(pmg_content)
                            self.production_method_groups_texture[pmg_name] = pmg_type
                            
                            # 提取生产方法（按定义顺序），处理嵌套大括号
                            pm_pattern = r'production_methods\s*=\s*\{([^}]*)\}'
                            pm_match = re.search(pm_pattern, pmg_content, re.DOTALL)
                            
                            if pm_match:
                                pm_content = pm_match.group(1)
                                # 使用更精确的匹配，只匹配有效的生产方法名
                                production_methods = re.findall(r'(\w+)', pm_content)
                                production_methods = [name for name in production_methods if name and not name.isspace()]  # 过滤空名和空格
                                self.production_method_groups_data[pmg_name] = production_methods
        except Exception as e:
            print(f"加载生产方法组数据时出错：{e}")
    
    def analyze_production_method_goods(self):
        """分析生产方法中的物资输入输出关系"""
        pm_dir = os.path.join(self.base_path, "production_methods")
        
        try:
            for filename in os.listdir(pm_dir):
                if filename.endswith('.txt') and not filename.startswith('.'):
                    filepath = os.path.join(pm_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # 处理BOM字符：移除文件开头的BOM字符
                        if content.startswith('\ufeff'):
                            content = content[1:]
                        
                        # 找到所有生产方法定义
                        pm_blocks = re.findall(r'^(\w+)\s*=\s*\{([\s\S]*?)^\}$', content, re.MULTILINE)
                        
                        for pm_name, pm_content in pm_blocks:
                            input_goods = {}
                            output_goods = {}
                            
                            # 直接在生产方法内容中查找物资输入输出及数值
                            input_pattern = r'goods_input_(\w+)_add\s*=\s*(-?\d+)'
                            output_pattern = r'goods_output_(\w+)_add\s*=\s*(-?\d+)'
                            
                            # 提取输入物资及数值
                            input_matches = re.findall(input_pattern, pm_content)
                            for goods_name, value in input_matches:
                                # 输入物资：转换正负号（负值变正值，正值变负值）
                                numeric_value = int(value)
                                input_goods[goods_name] = -numeric_value
                            
                            # 提取输出物资及数值
                            output_matches = re.findall(output_pattern, pm_content)
                            for goods_name, value in output_matches:
                                # 输出物资：直接使用原始值
                                output_goods[goods_name] = int(value)
                            
                            # 使用生产方法名作为键
                            self.goods_relations[pm_name] = {
                                "input": input_goods,
                                "output": output_goods
                            }
        except Exception as e:
            print(f"分析生产方法物资关系时出错：{e}")
    
    def generate_table(self):
        """生成表格数据"""
        print("开始提取数据...")
        
        # 提取所有数据
        self.goods_list = self.extract_goods_names()
        self.extract_buildings_hierarchy()
        self.analyze_production_method_goods()
        
        print(f"找到 {len(self.goods_list)} 个物资")
        print(f"建立 {len(self.buildings_hierarchy)} 条层级关系")
        
        # 调试：检查物资关系分析结果
        print(f"分析到 {len(self.goods_relations)} 个生产方法的物资关系")
        
        # 生成表头
        headers = ["buildings", "production_method_groups", "production_methods", "type", "required_construction"] + self.goods_list
        
        # 生成表格数据
        table_data = []
        
        # 为每个层级关系创建行
        for hierarchy in self.buildings_hierarchy:
            building = hierarchy['building']
            pmg = hierarchy['production_method_group']
            
            # 为每个生产方法创建一行
            for pm in hierarchy['production_methods']:
                # 获取pmg对应的type
                pmg_type = self.production_method_groups_texture.get(pmg, "other")
                # 获取建筑的required_construction值
                construction_cost = self.building_construction_costs.get(building, "")
                row = [building, pmg, pm, pmg_type, construction_cost]
                
                # 为每个物资列添加数值信息
                for goods in self.goods_list:
                    value_info = ""
                    if pm in self.goods_relations:
                        input_value = 0
                        output_value = 0
                        
                        # 获取输入值（如果存在）
                        if goods in self.goods_relations[pm]["input"]:
                            input_value = self.goods_relations[pm]["input"][goods]
                        
                        # 获取输出值（如果存在）
                        if goods in self.goods_relations[pm]["output"]:
                            output_value = self.goods_relations[pm]["output"][goods]
                        
                        # 计算净影响：输入值 + 输出值 （虽然目前没有这种PM，但是某些游戏设计中是可能存在的）
                        net_value = input_value + output_value
                        
                        # 如果净影响不为0，显示数值
                        if net_value != 0:
                            value_info = str(net_value)
                    
                    row.append(value_info)
                
                table_data.append(row)
        
        return headers, table_data
    
    def save_to_csv(self, filename: str = "victoria3_building_pm_goods.csv"):
        """保存为CSV文件"""
        headers, table_data = self.generate_table()
        
        try:
            with open(filename, 'w', encoding='utf-8-sig') as f:
                # 写入表头
                f.write(','.join(headers) + '\n')
                
                # 写入数据
                for row in table_data:
                    f.write(','.join(row) + '\n')
            
            print(f"表格已保存到 {filename}")
        except Exception as e:
            print(f"保存CSV文件时出错：{e}")
    
def main():
    """主函数"""
    analyzer = Victoria3DataAnalyzer()
    
    print("维多利亚3建筑生产方法物资关系分析程序")
    print("=" * 50)
    
    # 生成并保存表格
    analyzer.save_to_csv()
    
    print("\n程序执行完成！")

if __name__ == "__main__":
    main()
