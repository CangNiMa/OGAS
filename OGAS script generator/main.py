#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Victoria 3 PM Goods to Script Values Converter
将带有生产方式和物资数据的表格转化为游戏内的script_values
"""

import csv
import os
import re

# 缓存pm_goods.csv数据，避免重复读取
_pm_goods_cache = None

def read_pm_goods_csv():
    global _pm_goods_cache
    
    # 如果已经缓存过数据，直接返回缓存
    if _pm_goods_cache is not None:
        return _pm_goods_cache
    
    input_file = 'pm_goods.csv'
    
    try:
        # 读取CSV文件
        with open(input_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
        
        # 检查文件是否为空
        if len(rows) < 2:
            print("错误：CSV文件为空或格式不正确")
            return []
        
        # 缓存数据并返回
        _pm_goods_cache = rows
        return rows
        
    except FileNotFoundError:
        print(f"错误：找不到输入文件 {input_file}")
        return []
    except Exception as e:
        print(f"读取pm_goods.csv时发生错误：{e}")
        return []

def read_goods_from_file():
    """从goods/00_goods.txt文件中读取物资名称列表"""
    goods_file = 'goods/00_goods.txt'
    goods_list = []
    
    try:
        with open(goods_file, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # 使用正则表达式匹配物资定义：物资名称 = {
        pattern = r'^(\w+)\s*=\s*\{'
        matches = re.findall(pattern, content, re.MULTILINE)
        
        # 过滤掉注释和空行，只保留有效的物资名称
        for match in matches:
            if match and not match.startswith('#'):
                goods_list.append(match)
        
        print(f"从 {goods_file} 中读取了 {len(goods_list)} 个物资")
        return goods_list
        
    except FileNotFoundError:
        print(f"错误：找不到物资文件 {goods_file}")
        return []
    except Exception as e:
        print(f"读取物资文件时发生错误：{e}")
        return []

def convert_pm_goods_to_script_values():
    """将pm_goods.csv转换为script_values格式"""
    
    # 输出文件路径
    output_file = 'script_values/AUTO_database_pm_goods.txt'
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 从文件读取物资列对应的英文名称
    goods_columns = read_goods_from_file()
    
    # 如果读取失败，使用空列表
    if not goods_columns:
        print("警告：无法读取物资列表，使用空列表")
        goods_columns = []
    
    try:
        # 使用统一函数读取CSV文件
        rows = read_pm_goods_csv()
        
        # 检查文件是否为空
        if len(rows) < 2:
            print("错误：CSV文件为空或格式不正确")
            return
        
        # 构建数据结构：每个生产方式组对应的物资和生产方式
        production_group_data = {}
        
        # 处理每一行数据（跳过标题行）
        for row in rows[1:]:
            if len(row) < 3:
                continue
            
            building_type = row[0].strip()  # 建筑类型（第1列）
            pmg_name = row[1].strip()  # 生产方式组名称（第2列）
            pm_name = row[2].strip()  # 生产方式名称（第3列）
            
            # 初始化生产方式组数据
            if pmg_name not in production_group_data:
                production_group_data[pmg_name] = {
                    'building_type': building_type,
                    'production_methods': [],
                    'goods_data': {}
                }
            
            # 添加生产方式
            if pm_name not in production_group_data[pmg_name]['production_methods']:
                production_group_data[pmg_name]['production_methods'].append(pm_name)
            
            # 处理每个物资列
            for i, goods_name in enumerate(goods_columns):
                if i + 5 < len(row):  # 确保列索引有效（物资数据从第6列开始）
                    goods_value = row[i + 5].strip()  # 物资数值（列索引从5开始）
                    
                    # 记录物资数据（包括空值）
                    if goods_name not in production_group_data[pmg_name]['goods_data']:
                        production_group_data[pmg_name]['goods_data'][goods_name] = {}
                    
                    # 存储生产方式对应的物资数值（如果为空则存储为0）
                    if goods_value and goods_value != '':
                        production_group_data[pmg_name]['goods_data'][goods_name][pm_name] = goods_value
                    else:
                        production_group_data[pmg_name]['goods_data'][goods_name][pm_name] = '0'
        
        # 生成输出文件
        with open(output_file, 'w', encoding='utf-8-sig') as outfile:
            # 为每个生产方式组中的每个物资生成完整条目
            for pmg_name, pmg_data in production_group_data.items():
                production_methods = pmg_data['production_methods']
                goods_data = pmg_data['goods_data']
                
                # 收集该PMG实际使用的物资列表（有非零值的物资）
                used_goods = [goods for goods, pm_values in goods_data.items() 
                            if any(v != '0' for v in pm_values.values())]
                
                # 为每个实际使用的物资生成所有生产方式的条目
                for goods_name in used_goods:
                    pm_values = goods_data[goods_name]
                    for pm_name in production_methods:
                        # 获取物资数值，如果没有则使用0
                        goods_value = pm_values.get(pm_name, '0')
                        
                        # 生成条目：pm名_物资名=物资数
                        entry = f"{pm_name}_{goods_name}={goods_value}\n"
                        outfile.write(entry)
        
        print(f"转换完成！输出文件：{output_file}")
        print(f"共处理了 {len(production_group_data)} 个生产方式组")
        
    except Exception as e:
        print(f"转换过程中发生错误：{e}")

def generate_base_goods_price_script():
    """生成基础物资价格脚本"""
    
    goods_file = 'goods/00_goods.txt'
    output_file = 'script_values/AUTO_database_base_goods_price.txt'
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        with open(goods_file, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 使用正则表达式匹配物资定义和价格信息
        # 匹配模式：物资名称 = { ... cost = 价格 ... }
        pattern = r'^(\w+)\s*=\s*\{[^}]*?cost\s*=\s*(\d+)'
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        
        # 生成输出文件
        with open(output_file, 'w', encoding='utf-8-sig') as outfile:
            for goods_name, cost_value in matches:
                # 生成条目：物资名称_base_price = 价格
                entry = f"{goods_name}_base_price = {cost_value}\n"
                outfile.write(entry)
        
        print(f"基础物资价格脚本生成完成！输出文件：{output_file}")
        print(f"共处理了 {len(matches)} 个物资的价格信息")
        
    except FileNotFoundError:
        print(f"错误：找不到物资文件 {goods_file}")
    except Exception as e:
        print(f"生成基础物资价格脚本时发生错误：{e}")

def generate_price_prediction_script():
    """生成物资价格预测计算器脚本"""
    
    output_file = 'script_values/AUTO_price_prediction.txt'
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 从文件读取物资列对应的英文名称
    goods_columns = read_goods_from_file()
    
    # 如果读取失败，使用空列表
    if not goods_columns:
        print("警告：无法读取物资列表，使用空列表")
        goods_columns = []
    
    try:
        # 生成输出文件
        with open(output_file, 'w', encoding='utf-8-sig') as outfile:
            for goods_name in goods_columns:
                # 为每个物资生成价格预测计算器
                prediction_script = f"""{goods_name}_price_prediction = {{
    if = {{
        limit = {{
            scope:state_{goods_name}_production_prediction < scope:state_{goods_name}_consumption_prediction
        }}
        value = scope:state_{goods_name}_production_prediction
        subtract = scope:state_{goods_name}_consumption_prediction
        divide = {{
            value = scope:state_{goods_name}_production_prediction
            min = 0.1
        }}
        multiply = -0.75
        max = 0.75
        add = 1
    }}
    else_if = {{
        limit = {{
            scope:state_{goods_name}_production_prediction > scope:state_{goods_name}_consumption_prediction
        }}
        value = scope:state_{goods_name}_production_prediction
        subtract = scope:state_{goods_name}_consumption_prediction
        divide = {{
            value = scope:state_{goods_name}_consumption_prediction
            min = 0.1
        }}
        multiply = -0.75
        min = -0.75
        add = 1
    }}
    else = {{
        value = 1
    }}
    multiply = {{
        value = 1
        subtract = {{
            value = state.modifier:state_market_access_price_impact
            multiply = state.market_access
        }}
        multiply = {goods_name}_base_price
    }}
    add = {{
        value = state.modifier:state_market_access_price_impact
        multiply = state.market_access
        multiply = {goods_name}_base_price
        multiply = {{
            value = {{
                if = {{
                    limit = {{
                        scope:market_{goods_name}_production_prediction < scope:market_{goods_name}_consumption_prediction
                    }}
                    value = scope:market_{goods_name}_production_prediction
                    subtract = scope:market_{goods_name}_consumption_prediction
                    divide = {{
                        value = scope:market_{goods_name}_production_prediction
                        min = 0.1
                    }}
                    multiply = -0.75
                    max = 0.75
                    add = 1
                }}
                else_if = {{
                    limit = {{
                        scope:market_{goods_name}_production_prediction > scope:market_{goods_name}_consumption_prediction
                    }}
                    value = scope:market_{goods_name}_production_prediction
                    subtract = scope:market_{goods_name}_consumption_prediction
                    divide = {{
                        value = scope:market_{goods_name}_consumption_prediction
                        min = 0.1
                    }}
                    multiply = -0.75
                    min = -0.75
                    add = 1
                }}
                else = {{
                    value = 1
                }}
            }}
        }}
    }}
}}

"""
                outfile.write(prediction_script)
        
        print(f"物资价格预测计算器生成完成！输出文件：{output_file}")
        print(f"共为 {len(goods_columns)} 个物资生成了价格预测计算器")
        
    except Exception as e:
        print(f"生成物资价格预测计算器时发生错误：{e}")

def generate_goods_origin_script():
    """生成物资原始情况计算器脚本"""
    
    output_file = 'script_values/AUTO_goods_origin.txt'
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 从文件读取物资列对应的英文名称
    goods_columns = read_goods_from_file()
    
    # 如果读取失败，使用空列表
    if not goods_columns:
        print("警告：无法读取物资列表，使用空列表")
        goods_columns = []
    
    try:
        # 使用统一函数读取CSV文件
        rows = read_pm_goods_csv()
        
        if len(rows) < 2:
            print("错误：CSV文件为空或格式不正确")
            return
        
        # 构建数据结构：每个生产方式组对应的物资和生产方式
        production_group_data = {}
        
        # 处理每一行数据（跳过标题行）
        for row in rows[1:]:
            if len(row) < 3:
                continue
            
            building_type = row[0].strip()  # 建筑类型（第1列）
            pmg_name = row[1].strip()  # 生产方式组名称（第2列）
            pm_name = row[2].strip()  # 生产方式名称（第3列）
            
            # 初始化生产方式组数据
            if pmg_name not in production_group_data:
                production_group_data[pmg_name] = {
                    'building_type': building_type,
                    'production_methods': [],
                    'goods_data': {}
                }
            
            # 添加生产方式
            if pm_name not in production_group_data[pmg_name]['production_methods']:
                production_group_data[pmg_name]['production_methods'].append(pm_name)
            
            # 处理每个物资列
            for i, goods_name in enumerate(goods_columns):
                if i + 5 < len(row):  # 确保列索引有效（物资数据从第6列开始）
                    goods_value = row[i + 5].strip()  # 物资数值（列索引从5开始）
                    
                    # 只处理有实际数值的条目（非空且非零）
                    if goods_value and goods_value != '0' and goods_value != '0.0':
                        if goods_name not in production_group_data[pmg_name]['goods_data']:
                            production_group_data[pmg_name]['goods_data'][goods_name] = []
                        production_group_data[pmg_name]['goods_data'][goods_name].append((pm_name, goods_value))
        
        # 生成输出文件
        with open(output_file, 'w', encoding='utf-8-sig') as outfile:
            for pmg_name, pmg_data in production_group_data.items():
                building_type = pmg_data['building_type']
                production_methods = pmg_data['production_methods']
                goods_data = pmg_data['goods_data']
                
                # 为每个物资生成计算器
                for goods_name, pm_list in goods_data.items():
                    # 生成 pmg_生产组名_物资名_current 计算器
                    current_script = f"""{pmg_name}_{goods_name}_current = {{
    if = {{
        limit = {{
            has_active_production_method = {production_methods[0]}
        }}
        value = {production_methods[0]}_{goods_name}
    }}
"""
                    
                    # 添加其他生产方式的 else_if 块
                    for i in range(1, len(production_methods)):
                        current_script += f"""    else_if = {{
        limit = {{
            has_active_production_method = {production_methods[i]}
        }}
        value = {production_methods[i]}_{goods_name}
    }}
"""
                    
                    # 添加 else 块和结尾
                    current_script += f"""    else = {{
        value = 0.0
    }}
    multiply = building_work_efficiency
}}

"""
                    
                    # 生成其他4个计算器
                    origin_scripts = f"""state_{goods_name}_production_if_no_{pmg_name} = {{
\tvalue = state.sg:{goods_name}.state_goods_production
    if = {{
        limit = {{
            {pmg_name}_{goods_name}_current > 0.0
        }}
\tsubtract = {pmg_name}_{goods_name}_current
    }}
}}

state_{goods_name}_consumption_if_no_{pmg_name} = {{
\tvalue = state.sg:{goods_name}.state_goods_consumption
    if = {{
        limit = {{
            {pmg_name}_{goods_name}_current < 0.0
        }}
\tadd = {pmg_name}_{goods_name}_current
    }}
}}

market_{goods_name}_production_if_no_{pmg_name} = {{
\tvalue = market.mg:{goods_name}.market_goods_sell_orders
    if = {{
        limit = {{
            {pmg_name}_{goods_name}_current > 0.0
        }}
\tsubtract = {pmg_name}_{goods_name}_current
        multiply = state.market_access
    }}
}}

market_{goods_name}_consumption_if_no_{pmg_name} = {{
\tvalue = market.mg:{goods_name}.market_goods_buy_orders
    if = {{
        limit = {{
            {pmg_name}_{goods_name}_current < 0.0
        }}
\tadd = {pmg_name}_{goods_name}_current
        multiply = state.market_access
    }}
}}

"""
                    
                    # 写入文件
                    outfile.write(current_script)
                    outfile.write(origin_scripts)
        
        print(f"物资原始情况计算器生成完成！输出文件：{output_file}")
        print(f"共处理了 {len(production_group_data)} 个生产方式组")
        
    except Exception as e:
        print(f"生成物资原始情况计算器时发生错误：{e}")

def generate_building_profit_prediction_script():
    """生成建筑利润预测计算器脚本"""
    
    output_file = 'script_values/AUTO_building_profit_prediction.txt'
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 从文件读取物资列对应的英文名称
    goods_columns = read_goods_from_file()
    
    # 如果读取失败，使用空列表
    if not goods_columns:
        print("警告：无法读取物资列表，使用空列表")
        goods_columns = []
    
    try:
        # 使用统一函数读取CSV文件
        rows = read_pm_goods_csv()
        
        if len(rows) < 2:
            print("错误：CSV文件为空或格式不正确")
            return
        
        # 构建数据结构：每个生产方式对应的物资数据，使用pmg_name和pm_name的组合作为键
        production_method_data = {}
        
        # 处理每一行数据（跳过标题行）
        for row in rows[1:]:
            if len(row) < 3:
                continue
            
            building_type = row[0].strip()  # 建筑类型（第1列）
            pmg_name = row[1].strip()  # 生产方式组名称（第2列）
            pm_name = row[2].strip()  # 生产方式名称（第3列）
            
            # 使用pmg_name和pm_name的组合作为唯一键
            key = f"{pmg_name}_{pm_name}"
            
            # 初始化生产方式数据
            if key not in production_method_data:
                production_method_data[key] = {
                    'building_type': building_type,
                    'pmg_name': pmg_name,
                    'pm_name': pm_name,
                    'goods_data': {}
                }
            
            # 处理每个物资列
            for i, goods_name in enumerate(goods_columns):
                if i + 5 < len(row):  # 确保列索引有效（物资数据从第6列开始）
                    goods_value = row[i + 5].strip()  # 物资数值（列索引从5开始）
                    
                    # 只记录有实际数值的条目（非空且非零）
                    if goods_value and goods_value != '0' and goods_value != '0.0':
                        production_method_data[key]['goods_data'][goods_name] = goods_value
        
        # 生成输出文件
        with open(output_file, 'w', encoding='utf-8-sig') as outfile:
            # 为每个生产方式生成利润预测计算器
            for key, pm_data in production_method_data.items():
                pmg_name = pm_data['pmg_name']
                pm_name = pm_data['pm_name']
                goods_data = pm_data['goods_data']
                
                # 生成计算器开头
                profit_script = f"""{pmg_name}_{pm_name}_profit_prediction = {{
    value = 0
"""
                
                # 为每个物资生成 add 块
                for goods_name, goods_value in goods_data.items():
                    # 根据物资数值的正负生成不同的逻辑
                    if float(goods_value) > 0:  # 生产物资
                        profit_script += f"""    add = {{
        value = {pm_name}_{goods_name}
        multiply = building_work_efficiency
        save_temporary_value_as = {pm_name}_{goods_name}_prediction
        value = state_{goods_name}_production_if_no_{pmg_name}
        add = scope:{pm_name}_{goods_name}_prediction
        save_temporary_value_as = state_{goods_name}_production_prediction
        value = state_{goods_name}_consumption_if_no_{pmg_name}
        save_temporary_value_as = state_{goods_name}_consumption_prediction
        value = market_{goods_name}_production_if_no_{pmg_name}
        add = scope:{pm_name}_{goods_name}_prediction
        save_temporary_value_as = market_{goods_name}_production_prediction
        value = market_{goods_name}_consumption_if_no_{pmg_name}
        save_temporary_value_as = market_{goods_name}_consumption_prediction
        value = {goods_name}_price_prediction
        multiply = scope:{pm_name}_{goods_name}_prediction
    }}
"""
                    else:  # 消费物资（负值）
                        profit_script += f"""    add = {{
        value = {pm_name}_{goods_name}
        multiply = building_work_efficiency
        save_temporary_value_as = {pm_name}_{goods_name}_prediction
        value = state_{goods_name}_production_if_no_{pmg_name}
        save_temporary_value_as = state_{goods_name}_production_prediction
        value = state_{goods_name}_consumption_if_no_{pmg_name}
        subtract = scope:{pm_name}_{goods_name}_prediction
        save_temporary_value_as = state_{goods_name}_consumption_prediction
        value = market_{goods_name}_production_if_no_{pmg_name}
        save_temporary_value_as = market_{goods_name}_production_prediction
        value = market_{goods_name}_consumption_if_no_{pmg_name}
        subtract = scope:{pm_name}_{goods_name}_prediction
        save_temporary_value_as = market_{goods_name}_consumption_prediction
        value = {goods_name}_price_prediction
        multiply = scope:{pm_name}_{goods_name}_prediction
    }}
"""
                
                # 添加结尾
                profit_script += f"""    divide = level
}}

{pmg_name}_{pm_name}_profit_prediction_weighted = {{
    value = {pmg_name}_{pm_name}_profit_prediction
    multiply = owner.var:cnm_upgrade_tolerance_pm_manager
}}

"""
                
                # 写入文件
                outfile.write(profit_script)
        
        print(f"建筑利润预测计算器生成完成！输出文件：{output_file}")
        print(f"共为 {len(production_method_data)} 个生产方式生成了利润预测计算器")
        
    except Exception as e:
        print(f"生成建筑利润预测计算器时发生错误：{e}")

def generate_pm_balance_script():
    """生成PM排序计算器脚本"""
    
    balance_output_file = 'scripted_effects/AUTO_PM_balance.txt'
    upgrade_output_file = 'scripted_effects/AUTO_PM_upgrade.txt'
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(balance_output_file), exist_ok=True)
    os.makedirs(os.path.dirname(upgrade_output_file), exist_ok=True)
    
    try:
        # 使用统一函数读取CSV文件
        rows = read_pm_goods_csv()
        
        if len(rows) < 2:
            print("错误：CSV文件为空或格式不正确")
            return
        
        # 构建数据结构：按type分类的生产方式组数据
        balance_data = {}  # type为balance的数据
        upgrade_data = {}  # type为upgrade的数据
        
        # 处理每一行数据（跳过标题行）
        for row in rows[1:]:
            # 检查行长度是否足够（至少需要4列，包括type列）
            if len(row) < 4:
                continue
            
            type_value = row[3].strip()  # type列（第4列）
            building_type = row[0].strip()  # 建筑类型（第1列）
            pmg_name = row[1].strip()  # 生产方式组名称（第2列）
            pm_name = row[2].strip()  # 生产方式名称（第3列）
            
            # 根据type值分类处理
            if type_value == "balance":
                if pmg_name not in balance_data:
                    balance_data[pmg_name] = {
                        'building_type': building_type,
                        'production_methods': []
                    }
                if pm_name not in balance_data[pmg_name]['production_methods']:
                    balance_data[pmg_name]['production_methods'].append(pm_name)
            
            elif type_value == "upgrade":
                if pmg_name not in upgrade_data:
                    upgrade_data[pmg_name] = {
                        'building_type': building_type,
                        'production_methods': []
                    }
                if pm_name not in upgrade_data[pmg_name]['production_methods']:
                    upgrade_data[pmg_name]['production_methods'].append(pm_name)
        
        # 生成balance类型输出文件
        if balance_data:
            with open(balance_output_file, 'w', encoding='utf-8-sig') as outfile:
                # 添加文件开头
                outfile.write("PM_balance = {\n")
                
                # 为每个生产方式组生成排序计算器
                for pmg_name, pmg_data in balance_data.items():
                    building_type = pmg_data['building_type']
                    production_methods = pmg_data['production_methods']
                    
                    # 为每个生产方式生成 ordered_scope_state 块
                    for pm_name in production_methods:
                        # 生成 ordered_scope_state 块开头
                        balance_script = f"""    ordered_scope_state = {{
        limit = {{
            has_active_building = {building_type}
            b:{building_type}.occupancy > 0.01
            can_activate_production_method = {{
                building_type = {building_type}
                production_method = {pm_name}
            }}
"""
                        
                        # 为每个非当前生产方式生成 trigger_if 块
                        for other_pm in production_methods:
                            if other_pm != pm_name:
                                balance_script += f"""            trigger_if = {{
                limit = {{
                    or = {{
                        can_activate_production_method = {{
                            building_type = {building_type}
                            production_method = {other_pm}
                        }}
                        is_production_method_active = {{
                            building_type = {building_type}
                            production_method = {other_pm}
                        }}
                    }}
                }}
                b:{building_type}.{pmg_name}_{pm_name}_profit_prediction > b:{building_type}.{pmg_name}_{other_pm}_profit_prediction_weighted
            }}
"""
                        
                        # 生成 ordered_scope_state 块结尾
                        balance_script += f"""        }}
        order_by = b:{building_type}.{pmg_name}_{pm_name}_profit_prediction
        max = owner.var:cnm_pm_manage_amount
        check_range_bounds = no
        activate_production_method = {{
            building_type = {building_type}
            production_method = {pm_name}
        }}
    }}
"""
                        
                        # 写入文件
                        outfile.write(balance_script)
                
                # 添加文件结尾
                outfile.write("}\n")
            
            print(f"PM平衡计算器生成完成！输出文件：{balance_output_file}")
            print(f"共为 {len(balance_data)} 个生产方式组生成了平衡计算器")
        else:
            print("未找到type为balance的数据，跳过生成平衡计算器")
        
        # 生成upgrade类型输出文件
        if upgrade_data:
            with open(upgrade_output_file, 'w', encoding='utf-8-sig') as outfile:
                # 添加文件开头
                outfile.write("PM_upgrade = {\n")
                
                # 为每个生产方式组生成升级计算器
                for pmg_name, pmg_data in upgrade_data.items():
                    building_type = pmg_data['building_type']
                    production_methods = pmg_data['production_methods']
                    
                    # 按生产方式在列表中的顺序推断层级关系（假设按顺序就是层级关系）
                    for i in range(len(production_methods) - 1):
                        current_pm = production_methods[i]
                        next_pm = production_methods[i + 1]
                        
                        # 生成升级块（从当前生产方式升级到下一级生产方式）
                        upgrade_script = f"""    ordered_scope_state = {{
        limit = {{
            has_active_building = {building_type}
            b:{building_type}.occupancy > 0.01
            is_production_method_active = {{
                building_type = {building_type}
                production_method = {current_pm}
            }}
            can_activate_production_method = {{
                building_type = {building_type}
                production_method = {next_pm}
            }}
            b:{building_type}.{pmg_name}_{next_pm}_profit_prediction_weighted > b:{building_type}.{pmg_name}_{current_pm}_profit_prediction
        }}
        order_by = b:{building_type}.{pmg_name}_{next_pm}_profit_prediction_weighted
        max = owner.var:cnm_pm_manage_amount
        check_range_bounds = no
        activate_production_method = {{
            building_type = {building_type}
            production_method = {next_pm}
        }}
    }}
"""
                        outfile.write(upgrade_script)
                
                # 添加文件结尾
                outfile.write("}\n")
            
            print(f"PM升级计算器生成完成！输出文件：{upgrade_output_file}")
            print(f"共为 {len(upgrade_data)} 个生产方式组生成了升级计算器")
        else:
            print("未找到type为upgrade的数据，跳过生成升级计算器")
        
    except Exception as e:
        print(f"生成PM计算器时发生错误：{e}")

def generate_building_control_scripts():
    """生成建筑控制流程脚本"""
    
    try:
        # 使用统一函数读取CSV文件
        rows = read_pm_goods_csv()
        
        if len(rows) < 2:
            print("错误：CSV文件为空或格式不正确")
            return
        
        # 提取所有唯一的建筑类型，保持出现顺序
        building_types = []
        seen = set()
        
        # 处理每一行数据（跳过标题行）
        for row in rows[1:]:
            if len(row) < 3:
                continue
            
            building_type = row[0].strip()  # 建筑类型（第1列）
            if building_type and building_type not in seen:
                seen.add(building_type)
                building_types.append(building_type)
        
        # 生成建筑按钮脚本
        buttons_output_file = 'scripted_buttons/AUTO_building_weight_button.txt'
        os.makedirs(os.path.dirname(buttons_output_file), exist_ok=True)
        
        with open(buttons_output_file, 'w', encoding='utf-8-sig') as outfile:
            for building_type in building_types:
                # 生成increase按钮
                increase_button = f"""increase_{building_type} = {{
    name = "increase_{building_type}"
    desc = "increase_{building_type}_desc"
    effect = {{
        change_variable = {{
            name = cnm_auto_construct_{building_type}
            add = 0.1
        }}
    }}
}}
"""
                # 生成decrease按钮
                decrease_button = f"""decrease_{building_type} = {{
    name = "decrease_{building_type}"
    desc = "decrease_{building_type}_desc"
    effect = {{
        change_variable = {{
            name = cnm_auto_construct_{building_type}
            add = -0.1
        }}
    }}
}}
"""
                outfile.write(increase_button)
                outfile.write(decrease_button)
        
        print(f"建筑按钮脚本生成完成！输出文件：{buttons_output_file}")
        
        # 生成脚本触发器
        triggers_output_file = 'scripted_triggers/AUTO_OGAS_scripted_triggers.txt'
        os.makedirs(os.path.dirname(triggers_output_file), exist_ok=True)
        
        with open(triggers_output_file, 'w', encoding='utf-8-sig') as outfile:
            # 生成OGAS_construct_building_configure
            outfile.write("OGAS_construct_building_configure = {\n")
            for building_type in building_types:
                trigger_if = f"""    trigger_if = {{
        limit = {{ 
            root.var:cnm_auto_construct_{building_type} <= 0
        }}
        not = {{
            is_building_type = {building_type}
        }}
    }}
"""
                outfile.write(trigger_if)
            outfile.write("}\n\n")
            
            # 生成OGAS_possible_building
            outfile.write("OGAS_possible_building = {\n")
            outfile.write("    or = {\n")
            for building_type in building_types:
                outfile.write(f"        is_building_type = {building_type}\n")
            outfile.write("    }\n")
            outfile.write("}\n")
        
        print(f"脚本触发器生成完成！输出文件：{triggers_output_file}")
        
        # 生成脚本效果
        effects_output_file = 'scripted_effects/AUTO_OGAS_construct.txt'
        os.makedirs(os.path.dirname(effects_output_file), exist_ok=True)
        
        with open(effects_output_file, 'w', encoding='utf-8-sig') as outfile:
            outfile.write("OGAS_find_best_profit_building = {\n")
            outfile.write("    while = {\n")
            outfile.write("        count = root.var:OGAS_building_unit_config\n")
            
            for building_type in building_types:
                if_block = f"""        if = {{
            limit = {{ 
                is_building_type = {building_type}
            }}
            state = {{
                start_building_construction = {building_type}
            }}
        }}
"""
                outfile.write(if_block)
            
            outfile.write("    }\n")
            outfile.write("}\n")
        
        print(f"脚本效果生成完成！输出文件：{effects_output_file}")
        
        # 生成建筑权重管理初始化名单
        weight_manager_output_file = 'scripted_effects/AUTO_building_weight_manager.txt'
        os.makedirs(os.path.dirname(weight_manager_output_file), exist_ok=True)
        
        with open(weight_manager_output_file, 'w', encoding='utf-8-sig') as outfile:
            # 添加文件开头
            outfile.write("OGAS_default_building_weight_manager = {\n")
            
            # 为每个建筑类型生成set_variable块
            for building_type in building_types:
                set_variable_block = f"""    set_variable = {{
        name = cnm_auto_construct_{building_type}
        value = 1
    }}
"""
                outfile.write(set_variable_block)
            
            # 添加文件结尾
            outfile.write("}\n")
        
        print(f"建筑权重管理初始化名单生成完成！输出文件：{weight_manager_output_file}")
        
        # 生成建筑权重计算器脚本
        profit_weight_output_file = 'script_values/AUTO_get_building_profit_weight.txt'
        os.makedirs(os.path.dirname(profit_weight_output_file), exist_ok=True)
        
        with open(profit_weight_output_file, 'w', encoding='utf-8-sig') as outfile:
            # 添加文件开头
            outfile.write("get_building_profit_weight = {\n")
            
            # 为每个建筑类型生成if块
            for building_type in building_types:
                if_block = f"""    if = {{
        limit = {{
            is_building_type = {building_type}
        }}
        value = owner.var:cnm_auto_construct_{building_type}
    }}
"""
                outfile.write(if_block)
            
            # 添加文件结尾
            outfile.write("}\n")
        
        print(f"建筑权重计算器生成完成！输出文件：{profit_weight_output_file}")
        print(f"共为 {len(building_types)} 个建筑类型生成了控制流程、初始化名单和权重计算器")
        
    except Exception as e:
        print(f"生成建筑控制流程时发生错误：{e}")

def generate_building_construction_cost_script():
    """生成建筑construction_cost脚本，基于pm_goods.csv中的required_construction数据"""
    
    output_file = 'script_values/AUTO_database_building_construction_cost.txt'
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        # 使用统一函数读取CSV文件
        rows = read_pm_goods_csv()
        
        if len(rows) < 2:
            print("错误：CSV文件为空或格式不正确")
            return
        
        # 构建数据结构：每个建筑对应的construction_cost类型
        building_construction_costs = {}
        
        # 处理每一行数据（跳过标题行）
        for row in rows[1:]:
            if len(row) < 5:
                continue
            
            building_name = row[0].strip()  # 建筑名称（第1列）
            construction_cost = row[4].strip()  # construction_cost类型（第5列）
            
            # 只处理有construction_cost数据的行
            if construction_cost and construction_cost != '':
                # 如果建筑还没有记录，或者需要更新construction_cost（取第一个非空值）
                if building_name not in building_construction_costs:
                    building_construction_costs[building_name] = construction_cost
        
        # 生成construction_cost脚本
        with open(output_file, 'w', encoding='utf-8-sig') as outfile:
            # 添加文件开头
            outfile.write("building_construction_cost = {\n")
            
            # 为每个建筑生成IF块
            for building_name, construction_cost in sorted(building_construction_costs.items()):
                outfile.write("    if = {\n")
                outfile.write("        limit = {\n")
                outfile.write(f"            is_building_type = {building_name}\n")
                outfile.write("        }\n")
                outfile.write(f"        value = {construction_cost}\n")
                outfile.write("    }\n")
            
            # 添加文件结尾
            outfile.write("}\n")
        
        print(f"建筑construction_cost脚本生成完成！输出文件：{output_file}")
        print(f"共处理了 {len(building_construction_costs)} 个建筑的construction_cost信息")
        
    except Exception as e:
        print(f"生成建筑construction_cost脚本时发生错误：{e}")

def generate_journal_entry_buttons():
    """生成journal entry按钮脚本，为每个建筑类型生成increase和decrease按钮"""
    
    output_file = 'journal_entries/AUTO_construct_building_manager.txt'
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        # 使用统一函数读取CSV文件
        rows = read_pm_goods_csv()
        
        if len(rows) < 2:
            print("错误：CSV文件为空或格式不正确")
            return
        
        # 提取所有唯一的建筑类型，保持出现顺序
        building_types = []
        seen = set()
        
        # 处理每一行数据（跳过标题行）
        for row in rows[1:]:
            if len(row) < 3:
                continue
            
            building_type = row[0].strip()  # 建筑类型（第1列）
            if building_type and building_type not in seen:
                seen.add(building_type)
                building_types.append(building_type)
        
        # 生成journal entry文件
        with open(output_file, 'w', encoding='utf-8-sig') as outfile:
            # 添加文件开头
            outfile.write("je_OGAS_building_weight_manager = {\n")
            outfile.write("    icon = \"gfx/interface/icons/event_icons/event_industry.dds\"\n")
            outfile.write("    group = je_group_internal_affairs\n")
            outfile.write("\n")
            
            # 为每个建筑类型生成increase和decrease按钮
            for building_type in building_types:
                # 生成increase按钮
                outfile.write(f"    scripted_button = increase_{building_type}\n")
                # 生成decrease按钮
                outfile.write(f"    scripted_button = decrease_{building_type}\n")
            
            # 添加文件结尾
            outfile.write("\tscripted_button = default_all_construct_building\n\tshould_be_pinned_by_default = yes\n}\n")
        
        print(f"journal entry按钮脚本生成完成！输出文件：{output_file}")
        print(f"共为 {len(building_types)} 个建筑类型生成了按钮配置")
        
    except Exception as e:
        print(f"生成journal entry按钮脚本时发生错误：{e}")

def main():
    """主函数"""
    print("Victoria 3 PM Goods to Script Values Converter")
    print("=" * 50)
    convert_pm_goods_to_script_values()
    print("=" * 50)
    generate_base_goods_price_script()
    print("=" * 50)
    generate_price_prediction_script()
    print("=" * 50)
    generate_goods_origin_script()
    print("=" * 50)
    generate_building_profit_prediction_script()
    print("=" * 50)
    generate_pm_balance_script()
    print("=" * 50)
    generate_building_control_scripts()
    print("=" * 50)
    generate_building_construction_cost_script()
    print("=" * 50)
    generate_journal_entry_buttons()

if __name__ == "__main__":
    main()
