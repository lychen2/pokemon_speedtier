# Pokemon Speed Tier Analysis Tool

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A comprehensive Python tool for analyzing competitive Pokemon battle speed tiers. This project fetches data from Smogon University's battle statistics and generates detailed speed tier reports in both Excel and HTML formats, complete with Pokemon sprites and usage statistics.

## Features

### 📊 **Multi-Format Export**
- **Excel Export**: Professional spreadsheets with dual worksheets (detailed data + summary statistics)
- **HTML Export**: Beautiful responsive tables with Pokemon sprites and interactive elements
- **Customizable Output**: Choose output directory and file naming conventions

### 🌐 **Comprehensive Data Coverage**
- **Multiple Formats**: VGC, Doubles OU, Singles OU, National Dex, Ubers, and 50+ competitive formats
- **Rating Tiers**: Support for all rating thresholds (0, 1500, 1630, 1695, 1760, 1825+)
- **Automatic Updates**: Fetches latest monthly data from Smogon and Pokemon Showdown
- **Multilingual Support**: English and Chinese Pokemon names

### 🎮 **Accurate Speed Calculations**
- **Level-Aware**: VGC/BSS formats use level 50, others use level 100
- **Nature Effects**: Proper handling of speed-boosting and speed-hindering natures
- **EV/IV Integration**: Realistic stat calculations based on competitive usage patterns
- **Usage Filtering**: Only includes speed configurations with >20% usage or most common setup

### 🎨 **Professional Presentation**
- **Pokemon Sprites**: Full sprite sheet integration for visual identification
- **Usage Visualization**: Color-coded usage bars and statistics
- **Responsive Design**: Mobile-friendly HTML output
- **Clean Formatting**: Professional styling with gradient themes

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/pokemon-speed-tiers.git
cd pokemon-speed-tiers

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

## Output File Structure

### Excel Export
- **Speed Tiers Sheet**: Detailed Pokemon data with usage rates, natures, EVs, and spreads
- **Speed Summary Sheet**: Statistical overview of each speed tier
- **Professional Formatting**: Color-coded headers, optimized column widths, and clean styling

### HTML Export
- **Responsive Design**: Mobile-friendly tables that adapt to screen size
- **Pokemon Sprites**: Visual Pokemon identification using official sprite sheets
- **Interactive Elements**: Hover effects, usage visualization bars, and color-coded natures
- **Statistics Dashboard**: Quick overview of speed tiers and Pokemon counts

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

## Requirements

- **Python 3.7+**
- **Dependencies**:
  - `pandas` - Data manipulation and Excel export
  - `openpyxl` - Excel file formatting  
  - `pyjson5` - JSON5 parsing
  - `requests` - HTTP requests for data fetching
  - `beautifulsoup4` - HTML parsing for web scraping

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

```bash
# Clone the repo
git clone https://github.com/lychen2/pokemon_speedtier.git
cd pokemon-speed-tiers

# Install dependencies
pip install -r requirements.txt

# Run the tool
python export_speed_tiers.py --list-formats
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Smogon University** - For providing comprehensive battle statistics
- **Pokemon Showdown** - For Pokemon data and sprite resources  
- **Game Freak/Nintendo** - For creating Pokemon (all Pokemon names and data are copyrighted by Nintendo)

## Support

If you encounter any issues or have feature requests, please [open an issue](https://github.com/your-username/pokemon-speed-tiers/issues) on GitHub.

---

**Note**: This tool is for educational and competitive analysis purposes. All Pokemon-related names, images, and data are copyrighted by Nintendo/Game Freak.