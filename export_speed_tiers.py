#!/usr/bin/env python3
"""
Speed Tiers Excel/HTML Exporter
独立的速度线Excel/HTML导出脚本

用法:
python export_speed_tiers.py [format_code] [rating_threshold] [options]

例如:
python export_speed_tiers.py gen9vgc2025regi 1630
python export_speed_tiers.py gen9doublesou 1825 --translate
python export_speed_tiers.py gen9vgc2025regi 1630 --html --translate

可选参数:
--translate, -t    使用中文翻译宝可梦名称
--output, -o       指定输出目录
--html, -h         导出为美化的HTML表格文件（包含宝可梦图标和样式）
--list-formats, -l 列出可用格式
"""

import os
import sys
import math
import re
import difflib
from datetime import datetime
import argparse
import pandas as pd
from openpyxl.styles import Font, Alignment, PatternFill
import pyjson5

# 数据目录
DATA_DIRECTORY = "stats"

# 全局变量存储数据
formatDisplayNames = {}
pokedexEntries = {}
spriteIndex = {}
translateNames = {}


def load_data_file(filepath, mode='r', encoding="utf8"):
    """加载JSON/JSON5文件数据"""
    if os.path.exists(filepath):
        with open(filepath, mode, encoding=encoding) as file:
            return pyjson5.loads(file.read())
    return None


def build_data_path(filename):
    """构建相对于数据目录的路径"""
    return os.path.join(DATA_DIRECTORY, filename)


def get_previous_year_month():
    """获取上个月的年份和月份"""
    now = datetime.now()
    month = now.month - 1
    year = now.year
    if month == 0:
        month = 12
        year -= 1
    return str(year), str(month).zfill(2)


def fetch_pokemon_usage_data(format_code, rating_threshold):
    """获取指定格式和评级的使用率数据"""
    year, month = get_previous_year_month()
    file_name = f"{year}-{month}-{format_code}-{rating_threshold}.json"
    file_path = build_data_path(file_name)
    usage_data = load_data_file(file_path)

    if usage_data:
        return usage_data.get("data", {})
    
    # 回退到前一个月
    previous_month = int(month) - 1
    previous_year = int(year)
    if previous_month == 0:
        previous_month = 12
        previous_year -= 1
    prev_file_name = f"{previous_year}-{str(previous_month).zfill(2)}-{format_code}-{rating_threshold}.json"
    prev_file_path = build_data_path(prev_file_name)
    usage_data = load_data_file(prev_file_path)
    if usage_data:
        print("Warning: Using outdated statistics data")
        return usage_data.get("data", {})
    return {}


def fuzzy_match(target, options):
    """使用模糊匹配找到最相似的选项"""
    normalized_options = {option.lower(): option for option in options}
    matches = difflib.get_close_matches(target.lower(), normalized_options.keys(), 10)
    return normalized_options[matches[0]] if matches else None


def calculate_stat_value(base, iv, ev, level, multiplier):
    """计算非HP属性值"""
    return math.floor((math.floor((2 * base + iv + math.floor(ev / 4)) * level / 100) + 5) * multiplier)


def calculate_speed_tiers(usage_data, format_code=""):
    """计算速度线数据"""
    speed_tiers = {}
    level = 50 if (("vgc" in format_code.lower()) or ("bss" in format_code.lower())) else 100
    
    # 速度相关性格
    speed_boost_natures = ["Timid", "Hasty", "Jolly", "Naive"]
    speed_nerf_natures = ["Brave", "Relaxed", "Quiet", "Sassy"]
    
    for pokemon_name, pokemon_data in usage_data.items():
        if pokemon_name == "ALL Pokemon":
            continue
            
        # 获取该宝可梦的种族值
        matched_name = fuzzy_match(pokemon_name, pokedexEntries.keys())
        if not matched_name:
            continue
            
        base_speed = pokedexEntries[matched_name]["baseStats"]["spe"]
        spreads = pokemon_data.get("Spreads", {})
        
        if not spreads:
            continue
        
        # 计算所有配招的速度值并找到最常见的速度
        speed_frequencies = {}
        total_spread_usage = sum(spreads.values())
        
        for spread, spread_usage in spreads.items():
            parts = spread.split(':')
            nature = parts[0]
            evs = list(map(int, parts[1].split('/')))
            speed_evs = evs[5]  # 速度是第6个属性值(索引5)
            
            # 基于性格计算速度倍率
            if nature in speed_boost_natures:
                multiplier = 1.1
            elif nature in speed_nerf_natures:
                multiplier = 0.9
            else:
                multiplier = 1.0
                
            # 如果速度被降低且没有努力值则使用0个体，否则使用31个体
            speed_iv = 0 if (multiplier == 0.9 and speed_evs == 0) else 31
            
            # 计算最终速度值
            speed_value = calculate_stat_value(base_speed, speed_iv, speed_evs, level, multiplier)
            
            # 记录速度频率和配招细节
            if speed_value not in speed_frequencies:
                speed_frequencies[speed_value] = {
                    'total_usage': 0,
                    'spreads': []
                }
            
            speed_frequencies[speed_value]['total_usage'] += spread_usage
            speed_frequencies[speed_value]['spreads'].append({
                'spread': spread,
                'nature': nature,
                'speed_evs': speed_evs,
                'usage': spread_usage
            })
        
        # 确定该宝可梦要包含哪些速度
        if speed_frequencies:
            usage_weight = pokemon_data.get("usage", 0)
            
            # 计算每个速度的百分比
            speeds_with_percentages = []
            for speed_value, speed_data in speed_frequencies.items():
                percentage = (speed_data['total_usage'] / total_spread_usage) * 100
                speeds_with_percentages.append((speed_value, speed_data, percentage))
            
            # 找到使用率>20%的速度
            high_usage_speeds = [(speed, data, perc) for speed, data, perc in speeds_with_percentages if perc > 20]
            
            # 如果多个速度使用率>20%则全部包含，否则只包含最常见的速度
            if len(high_usage_speeds) > 1:
                speeds_to_include = high_usage_speeds
            else:
                # 只包含最常见的速度
                most_common_speed = max(speed_frequencies.keys(), key=lambda x: speed_frequencies[x]['total_usage'])
                most_common_data = speed_frequencies[most_common_speed]
                most_common_percentage = (most_common_data['total_usage'] / total_spread_usage) * 100
                speeds_to_include = [(most_common_speed, most_common_data, most_common_percentage)]
            
            # 将每个选定的速度添加到速度线中
            for speed_value, speed_data, speed_percentage in speeds_to_include:
                # 找到实现该速度的最常见配招
                most_common_spread_for_speed = max(speed_data['spreads'], key=lambda x: x['usage'])
                
                # 存储到速度线中
                if speed_value not in speed_tiers:
                    speed_tiers[speed_value] = []
                    
                speed_tiers[speed_value].append({
                    'name': pokemon_name,
                    'usage': usage_weight,
                    'spread': most_common_spread_for_speed['spread'],
                    'base_speed': base_speed,
                    'nature': most_common_spread_for_speed['nature'],
                    'speed_evs': most_common_spread_for_speed['speed_evs'],
                    'speed_usage_ratio': speed_percentage / 100
                })
    
    # 在每个速度线内按使用率排序
    for speed_value in speed_tiers:
        speed_tiers[speed_value].sort(key=lambda x: x['usage'], reverse=True)
    
    # 转换为模板友好的排序列表格式
    sorted_speed_tiers = []
    for speed_value in sorted(speed_tiers.keys(), reverse=True):
        tier_pokemon = speed_tiers[speed_value]
        
        sorted_speed_tiers.append({
            'speed': speed_value,
            'pokemon_list': tier_pokemon,
            'total_usage': sum(p['usage'] for p in tier_pokemon)
        })
    
    return sorted_speed_tiers


def load_all_data(use_translation=False):
    """加载所有必要的数据文件"""
    global formatDisplayNames, pokedexEntries, translateNames
    
    # 加载格式显示名称
    formatDisplayNames = load_data_file(build_data_path("meta_names.json")) or {}
    
    # 加载宝可梦图鉴数据
    pokedexEntries = load_data_file(build_data_path("pokedex.json")) or {}
    
    # 如果需要翻译则加载翻译文件
    if use_translation:
        translateNames = load_data_file("translate.json") or {}
        print(f"Loaded {len(translateNames)} Pokemon translations")
    else:
        translateNames = {}
    
    print(f"Loaded {len(formatDisplayNames)} format names")
    print(f"Loaded {len(pokedexEntries)} Pokemon data")


def translate_pokemon_name(pokemon_name):
    """翻译宝可梦名称为中文（如果可用）"""
    if translateNames and pokemon_name in translateNames:
        return translateNames[pokemon_name]
    return pokemon_name


def get_pokemon_sprite_info(pokemon_name):
    """获取宝可梦图标信息，使用与app.py相同的逻辑"""
    # 加载图标索引（如果还未加载）
    global spriteIndex
    if not spriteIndex:
        spriteIndex = load_data_file(build_data_path("forms_index.json")) or {}
    
    if pokemon_name == "ALL Pokemon":
        return {'x': 0, 'y': 0, 'w': 40, 'h': 30}
    
    # 标准化宝可梦名称（与app.py中get_pokemon_sprite函数相同）
    word = pokemon_name.lower()
    word = re.sub(r'[^a-z0-9]+', '', word)
    
    sprite_num = 0
    if word in spriteIndex.keys():
        sprite_num = spriteIndex[word]
    elif word in pokedexEntries.keys():
        sprite_num = pokedexEntries[word].get("num", 0)
    
    # 计算sprite坐标 (每行12个sprite，每个sprite 40x30像素)
    row, col = divmod(sprite_num, 12)
    x = col * 40
    y = row * 30
    
    return {'x': x, 'y': y, 'w': 40, 'h': 30}


def export_to_html(speed_tiers_list, format_code, rating_threshold, output_dir="."):
    """导出速度线数据到美化的HTML表格文件"""
    if not speed_tiers_list:
        print("Error: No speed tier data to export")
        return None
    
    # 生成文件名
    format_display_name = formatDisplayNames.get(format_code, format_code)
    clean_format_name = re.sub(r'[^\w\-_\.]', '_', format_display_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Speed_Tiers_{clean_format_name}_{rating_threshold}_{timestamp}.html"
    filepath = os.path.join(output_dir, filename)
    
    # HTML模板
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Speed Tiers Table - {format_display_name} ({rating_threshold}+)</title>
    <style>
        :root {{
            --bg-color: #f2e6ff;
            --primary-color: #ff80bf;
            --secondary-color: #a64dff;
            --white-color: #ffffff;
            --dark-text: #330033;
            --light-bg: #faf0ff;
            --shadow-color: rgba(166, 77, 255, 0.2);
        }}
        
        body {{
            background-color: var(--bg-color);
            font-family: 'Arial', sans-serif;
            color: var(--dark-text);
            margin: 0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: var(--white-color);
            border-radius: 15px;
            box-shadow: 0 8px 32px var(--shadow-color);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
            color: var(--white-color);
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: bold;
        }}
        
        .header p {{
            margin: 10px 0 0 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        
        .stats-summary {{
            display: flex;
            justify-content: space-around;
            padding: 20px;
            background-color: var(--light-bg);
            border-bottom: 2px solid #e6ccff;
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 24px;
            font-weight: bold;
            color: var(--secondary-color);
        }}
        
        .stat-label {{
            font-size: 14px;
            color: var(--dark-text);
            margin-top: 5px;
        }}
        
        .table-container {{
            padding: 0;
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        
        th {{
            background: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
            color: var(--white-color);
            padding: 15px 10px;
            text-align: left;
            font-weight: bold;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        td {{
            padding: 12px 10px;
            border-bottom: 1px solid #e6ccff;
            vertical-align: middle;
        }}
        
        .speed-tier {{
            background-color: var(--light-bg);
            font-weight: bold;
            font-size: 16px;
            color: var(--secondary-color);
        }}
        
        .pokemon-row:hover {{
            background-color: rgba(166, 77, 255, 0.05);
        }}
        
        .pokemon-sprite {{
            width: 40px;
            height: 30px;
            background-image: url('pokemonicons-sheet.png');
            background-repeat: no-repeat;
            display: inline-block;
            vertical-align: middle;
            margin-right: 10px;
        }}
        
        .pokemon-name {{
            font-weight: bold;
            color: var(--dark-text);
        }}
        
        .usage-bar {{
            background-color: #e6ccff;
            border-radius: 10px;
            height: 20px;
            position: relative;
            overflow: hidden;
        }}
        
        .usage-fill {{
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
            height: 100%;
            border-radius: 10px;
            position: relative;
        }}
        
        .usage-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 11px;
            font-weight: bold;
            color: var(--dark-text);
            z-index: 2;
        }}
        
        .nature-positive {{
            color: #4caf50;
            font-weight: bold;
        }}
        
        .nature-negative {{
            color: #f44336;
            font-weight: bold;
        }}
        
        .nature-neutral {{
            color: var(--dark-text);
        }}
        
        @media (max-width: 768px) {{
            .container {{
                margin: 10px;
                border-radius: 10px;
            }}
            
            .header {{
                padding: 20px;
            }}
            
            .stats-summary {{
                flex-direction: column;
                gap: 15px;
            }}
            
            table {{
                font-size: 12px;
            }}
            
            th, td {{
                padding: 8px 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Speed Tiers Table</h1>
            <p>{format_display_name} - Rating {rating_threshold}+ - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-summary">
            <div class="stat-item">
                <div class="stat-number">{len(speed_tiers_list)}</div>
                <div class="stat-label">Speed Tiers</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{sum(len(tier['pokemon_list']) for tier in speed_tiers_list)}</div>
                <div class="stat-label">Pokemon Records</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{speed_tiers_list[0]['speed'] if speed_tiers_list else 0}</div>
                <div class="stat-label">Highest Speed</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{speed_tiers_list[-1]['speed'] if speed_tiers_list else 0}</div>
                <div class="stat-label">Lowest Speed</div>
            </div>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Speed</th>
                        <th>Pokemon</th>
                        <th>Usage Rate</th>
                        <th>Nature</th>
                        <th>Speed EVs</th>
                        <th>Base Speed</th>
                        <th>Reference EV Config</th>
                        <th>Speed Usage Rate</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # 计算最大使用率以进行比例缩放
    max_usage = max(pokemon['usage'] for tier in speed_tiers_list for pokemon in tier['pokemon_list']) if speed_tiers_list else 1
    
    # 速度相关性格
    speed_boost_natures = ["Timid", "Hasty", "Jolly", "Naive"]
    speed_nerf_natures = ["Brave", "Relaxed", "Quiet", "Sassy"]
    
    # 生成表格行
    for tier in speed_tiers_list:
        speed_value = tier['speed']
        
        for i, pokemon in enumerate(tier['pokemon_list']):
            translated_name = translate_pokemon_name(pokemon['name'])
            sprite_info = get_pokemon_sprite_info(pokemon['name'])
            
            # 计算使用率百分比和条形图宽度
            usage_percent = pokemon['usage'] * 100
            usage_width = min((pokemon['usage'] / max_usage) * 100, 100)
            
            # 性格颜色类
            nature = pokemon['nature']
            if nature in speed_boost_natures:
                nature_class = 'nature-positive'
            elif nature in speed_nerf_natures:
                nature_class = 'nature-negative'
            else:
                nature_class = 'nature-neutral'
            
            # 第一个宝可梦显示速度值，其他显示空
            speed_cell = f'<td class="speed-tier">{speed_value}</td>' if i == 0 else '<td></td>'
            
            html_content += f"""
                    <tr class="pokemon-row">
                        {speed_cell}
                        <td>
                            <div style="display: flex; align-items: center;">
                                <div class="pokemon-sprite" style="background-position: -{sprite_info['x']}px -{sprite_info['y']}px;"></div>
                                <span class="pokemon-name">{translated_name}</span>
                            </div>
                        </td>
                        <td>
                            <div class="usage-bar">
                                <div class="usage-fill" style="width: {usage_width}%;"></div>
                                <div class="usage-text">{usage_percent:.2f}%</div>
                            </div>
                        </td>
                        <td class="{nature_class}">{nature}</td>
                        <td>{pokemon['speed_evs']}</td>
                        <td>{pokemon['base_speed']}</td>
                        <td style="font-size: 12px; font-family: monospace;">{pokemon['spread']}</td>
                        <td>{pokemon['speed_usage_ratio'] * 100:.1f}%</td>
                    </tr>"""
    
    html_content += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""
    
    # 写入文件
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML file exported: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error exporting HTML file: {e}")
        return None


def export_to_excel(speed_tiers_list, format_code, rating_threshold, output_dir="."):
    """导出速度线数据到Excel文件"""
    if not speed_tiers_list:
        print("Error: No speed tier data to export")
        return None
    
    # 创建Excel数据结构
    excel_data = []
    
    for tier in speed_tiers_list:
        speed_value = tier['speed']
        
        for pokemon in tier['pokemon_list']:
            translated_name = translate_pokemon_name(pokemon['name'])
            excel_data.append({
                'Speed': speed_value,
                'Pokemon': translated_name,
                'Usage (%)': round(pokemon['usage'] * 100, 3),
                'Nature': pokemon['nature'],
                'Speed EVs': pokemon['speed_evs'],
                'Base Speed': pokemon['base_speed'],
                'Spread': pokemon['spread'],
                'Speed Usage Ratio (%)': round(pokemon['speed_usage_ratio'] * 100, 1)
            })
    
    # 创建DataFrame
    df = pd.DataFrame(excel_data)
    
    # 生成文件名
    format_display_name = formatDisplayNames.get(format_code, format_code)
    clean_format_name = re.sub(r'[^\w\-_\.]', '_', format_display_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Speed_Tiers_{clean_format_name}_{rating_threshold}_{timestamp}.xlsx"
    filepath = os.path.join(output_dir, filename)
    
    # 创建Excel文件
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # 写入主数据表
        df.to_excel(writer, sheet_name='Speed Tiers', index=False)
        
        # 获取工作簿和工作表
        workbook = writer.book
        worksheet = writer.sheets['Speed Tiers']
        
        # 设置列宽
        column_widths = {
            'A': 8,   # Speed
            'B': 20,  # Pokemon
            'C': 12,  # Usage (%)
            'D': 15,  # Nature
            'E': 12,  # Speed EVs
            'F': 12,  # Base Speed
            'G': 25,  # Spread
            'H': 18   # Speed Usage Ratio (%)
        }
        
        for column, width in column_widths.items():
            worksheet.column_dimensions[column].width = width
        
        # 添加标题格式
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # 创建汇总表
        summary_data = []
        for tier in speed_tiers_list:
            top_pokemon_name = tier['pokemon_list'][0]['name'] if tier['pokemon_list'] else ''
            translated_top_pokemon = translate_pokemon_name(top_pokemon_name)
            summary_data.append({
                'Speed': tier['speed'],
                'Pokemon Count': len(tier['pokemon_list']),
                'Total Usage (%)': round(tier['total_usage'] * 100, 3),
                'Top Pokemon': translated_top_pokemon
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Speed Summary', index=False)
        
        # 格式化汇总表
        summary_ws = writer.sheets['Speed Summary']
        summary_column_widths = {
            'A': 8,   # Speed
            'B': 15,  # Pokemon Count
            'C': 15,  # Total Usage (%)
            'D': 20   # Top Pokemon
        }
        
        for column, width in summary_column_widths.items():
            summary_ws.column_dimensions[column].width = width
        
        for cell in summary_ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
    
    print(f"Excel file exported: {filepath}")
    return filepath


def get_available_formats():
    """获取可用的格式列表"""
    if not os.path.exists(DATA_DIRECTORY):
        return []
    
    format_files = [f for f in os.listdir(DATA_DIRECTORY) if f.endswith("-0.json")]
    formats = []
    
    for file in format_files:
        parts = file.split("-")
        if len(parts) >= 3:
            format_code = parts[-2]
            display_name = formatDisplayNames.get(format_code, format_code)
            formats.append((format_code, display_name))
    
    return sorted(formats, key=lambda x: x[1])


def get_available_ratings(format_code):
    """获取指定格式的可用评级列表"""
    if not os.path.exists(DATA_DIRECTORY):
        return []
    
    files = [f for f in os.listdir(DATA_DIRECTORY) if format_code in f.split("-")]
    ratings = sorted([f.split("-")[-1].split(".")[0] for f in files], key=int)
    return ratings


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Export Pokemon battle speed tiers to Excel or HTML file")
    parser.add_argument("format", nargs='?', help="Format code (e.g.: gen9vgc2025regi)")
    parser.add_argument("rating", nargs='?', help="Rating threshold (e.g.: 1630)")
    parser.add_argument("--output", "-o", default=".", help="Output directory (default: current directory)")
    parser.add_argument("--list-formats", "-l", action="store_true", help="List available formats")
    parser.add_argument("--translate", "-t", action="store_true", help="Use Chinese translation for Pokemon names")
    parser.add_argument("--html", "-H", action="store_true", help="Export as beautiful HTML table file (with Pokemon icons)")
    
    args = parser.parse_args()
    
    # 加载数据
    print("Loading data...")
    load_all_data(use_translation=args.translate)
    
    # 如果请求列出格式
    if args.list_formats:
        formats = get_available_formats()
        print("\nAvailable formats:")
        for code, name in formats:
            ratings = get_available_ratings(code)
            print(f"  {code:<20} - {name} (Ratings: {', '.join(ratings)})")
        return
    
    # 如果没有提供参数，显示帮助
    if not args.format:
        print("Please provide format code, or use --list-formats to view available formats")
        print("Use --translate to enable Chinese translation")
        print("Use --html to export as beautiful HTML table file (with Pokemon icons)")
        formats = get_available_formats()[:5]  # 显示前5个格式作为示例
        print("\nExample formats:")
        for code, name in formats:
            print(f"  {code} - {name}")
        print("\nExample usage:")
        print("  python export_speed_tiers.py gen9vgc2025regi 1630 --translate")
        print("  python export_speed_tiers.py gen9vgc2025regi 1630 --html --translate")
        return
    
    format_code = args.format
    
    # 获取评级阈值
    if not args.rating:
        available_ratings = get_available_ratings(format_code)
        if not available_ratings:
            print(f"Error: No data files found for format '{format_code}'")
            return
        rating_threshold = available_ratings[-1]  # 使用最高评级
        print(f"Rating not specified, using highest rating: {rating_threshold}")
    else:
        rating_threshold = args.rating
    
    # 验证格式和评级
    available_ratings = get_available_ratings(format_code)
    if not available_ratings:
        print(f"错误: 格式 '{format_code}' 没有找到数据文件")
        return
    
    if rating_threshold not in available_ratings:
        print(f"Error: Rating '{rating_threshold}' is not available for format '{format_code}'")
        print(f"Available ratings: {', '.join(available_ratings)}")
        return
    
    # 获取使用率数据
    print(f"Getting usage data for {format_code} (rating {rating_threshold}+)...")
    usage_data = fetch_pokemon_usage_data(format_code, rating_threshold)
    
    if not usage_data:
        print("Error: Unable to get usage data")
        return
    
    print(f"Loaded data for {len(usage_data)} Pokemon")
    
    # 计算速度线
    print("Calculating speed tiers...")
    speed_tiers_list = calculate_speed_tiers(usage_data, format_code)
    
    if not speed_tiers_list:
        print("Error: No speed tier data calculated")
        return
    
    print(f"Calculated {len(speed_tiers_list)} speed tiers")
    
    # 选择导出格式并导出文件
    if args.html:
        print("Exporting HTML file...")
        if args.translate and translateNames:
            print("Using Chinese translation for HTML export")
        output_file = export_to_html(speed_tiers_list, format_code, rating_threshold, args.output)
        file_type = "HTML"
    else:
        print("Exporting Excel file...")
        if args.translate and translateNames:
            print("Using Chinese translation for Excel export")
        output_file = export_to_excel(speed_tiers_list, format_code, rating_threshold, args.output)
        file_type = "Excel"
    
    if output_file:
        print(f"{file_type} export successful! File saved at: {output_file}")
        print(f"Contains {sum(len(tier['pokemon_list']) for tier in speed_tiers_list)} Pokemon speed records")
    else:
        print(f"{file_type} export failed")


if __name__ == "__main__":
    main()