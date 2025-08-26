# Pokemon Speed Tier Analysis Tool

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A comprehensive Python tool for analyzing competitive Pokemon battle speed tiers. This project fetches data from Smogon University's battle statistics and generates detailed speed tier reports in both Excel and HTML formats, complete with Pokemon sprites and usage statistics.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/lychen2/pokemon_speedtier.git
cd pokemon_speedtier

# Install dependencies
pip install pandas openpyxl pyjson5 requests beautifulsoup4
```

### Basic Usage

```bash
# List all available formats
python export_speed_tiers.py --list-formats

# Export VGC 2025 speed tiers (1630+ rating) to Excel
python export_speed_tiers.py gen9vgc2025regi 1630

# Export Doubles OU speed tiers to HTML with Chinese names
python export_speed_tiers.py gen9doublesou 1825 --html --translate

# Update all data sources
python update_all_data.py
```

## Usage Examples

### Export Speed Tiers

```bash
# VGC 2025 Regulation I (most popular VGC format)
python export_speed_tiers.py gen9vgc2025regi 1630

# Doubles OU (competitive doubles)
python export_speed_tiers.py gen9doublesou 1825

# Singles OU (most popular singles format)
python export_speed_tiers.py gen9ou 1695

# National Dex (expanded roster format)
python export_speed_tiers.py gen9nationaldex 1760
```

### Filtering Options

```bash
# Export only Pokemon with usage rate >= 5%
python export_speed_tiers.py gen9vgc2025regi 1630 --min-usage 0.05

# Export only top 50 Pokemon by usage rate
python export_speed_tiers.py gen9vgc2025regi 1630 --top-n 50

# Combine filters: top 30 Pokemon with minimum 2% usage rate
python export_speed_tiers.py gen9vgc2025regi 1630 --top-n 30 --min-usage 0.02

# HTML output with filters and Chinese translation
python export_speed_tiers.py gen9vgc2025regi 1630 --html --translate --min-usage 0.03
```

### Output Formats

```bash
# Excel format (default)
python export_speed_tiers.py gen9vgc2025regi 1630

# HTML format with Pokemon sprites
python export_speed_tiers.py gen9vgc2025regi 1630 --html

# With Chinese translation
python export_speed_tiers.py gen9vgc2025regi 1630 --html --translate

# Custom output directory
python export_speed_tiers.py gen9vgc2025regi 1630 --output ./reports/
```

## Command Reference

### Main Export Tool (`export_speed_tiers.py`)

| Command | Description |
|---------|-------------|
| `python export_speed_tiers.py [format] [rating]` | Export speed tiers for specified format and rating |
| `--list-formats, -l` | List all available formats and their rating options |
| `--html, -H` | Export as HTML with Pokemon sprites (default: Excel) |
| `--translate, -t` | Use Chinese Pokemon names |
| `--output, -o [DIR]` | Specify output directory (default: current directory) |
| `--min-usage, -u [FLOAT]` | Filter Pokemon by minimum usage rate (e.g., 0.05 for 5%) |
| `--top-n, -n [INT]` | Export only top N Pokemon by usage rate |
| `--help` | Show detailed help message |

### Data Management (`update_all_data.py`)

```bash
# Update all data sources
python update_all_data.py

# This script will:
# - Fetch latest Pokemon data from Pokemon Showdown
# - Download battle statistics from Smogon University  
# - Update Pokemon sprite sheets
# - Clean outdated data files
# - Generate format name mappings
```

## Speed Calculation Details

### Formula
```
Speed = floor((floor((2 × BaseSpeed + IV + floor(EV/4)) × Level/100) + 5) × NatureMultiplier)
```

### Parameters
- **Level**: 50 for VGC/BSS formats, 100 for others
- **IV**: 31 (max) in most cases, 0 when speed is hindered and no EVs invested
- **EV**: Based on actual competitive usage patterns
- **Nature Multiplier**:
  - Speed+ natures (Timid, Hasty, Jolly, Naive): ×1.1
  - Speed- natures (Brave, Relaxed, Quiet, Sassy): ×0.9  
  - Neutral natures: ×1.0

### Data Filtering
- Includes speed configurations with >20% usage within that Pokemon
- For Pokemon without high-usage speeds, includes the most common configuration
- Sorted by speed value (highest to lowest)
- Within each tier, sorted by Pokemon usage rate

## Data Sources

- **Pokemon Data**: [Pokemon Showdown](https://play.pokemonshowdown.com)
- **Battle Statistics**: [Smogon University](https://www.smogon.com/stats/)
- **Sprite Images**: [Pokemon Showdown Sprites](https://play.pokemonshowdown.com/sprites/)
- **Format Information**: [Smogon Pokemon Showdown](https://github.com/smogon/pokemon-showdown)

## File Structure

```
pokemon-speed-tiers/
├── export_speed_tiers.py      # Main export tool
├── update_all_data.py         # Data management script
├── translate.json             # Pokemon name translations
├── pokemonicons-sheet.png     # Pokemon sprite sheet
├── stats/                     # Data directory
│   ├── pokedex.json          # Pokemon base stats
│   ├── forms_index.json      # Sprite positioning
│   ├── meta_names.json       # Format name mappings
│   └── YYYY-MM-format-rating.json  # Monthly battle stats
└── README.md                  # This file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Smogon University** - For providing comprehensive battle statistics
- **Pokemon Showdown** - For Pokemon data and sprite resources  
- **Game Freak/Nintendo** - For creating Pokemon (all Pokemon names and data are copyrighted by Nintendo)

---

**Note**: This tool is for educational and competitive analysis purposes. All Pokemon-related names, images, and data are copyrighted by Nintendo/Game Freak.