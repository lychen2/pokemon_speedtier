import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re
import pyjson5
import os
import difflib

def get_current_month_prefix():
    """Get the current month prefix for filtering files"""
    year = datetime.now().year
    month = datetime.now().month - 1
    if month == 0:
        month = 12
        year = year - 1
    return f"{year}-{str(month).zfill(2)}"

def clean_old_data():
    """Clean old data files that are not from the previous month"""
    current_prefix = get_current_month_prefix()
    stats_dir = "stats"
    
    if not os.path.exists(stats_dir):
        print(f"Stats directory {stats_dir} does not exist.")
        return
    
    # Find all JSON files with date patterns
    old_files = []
    for file in os.listdir(stats_dir):
        if file.endswith('.json') and '-' in file:
            # Skip core data files that don't have date patterns
            if file in ['pokedex.json', 'forms_index.json', 'meta_names.json', 'abilities.json', 'items.json', 'moves.json']:
                continue
            
            # Check if file starts with current month prefix
            if not file.startswith(current_prefix):
                # Verify it's actually a date-prefixed file
                parts = file.split('-')
                if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                    old_files.append(file)
    
    if not old_files:
        print("No old data files found to clean.")
        return
    
    print(f"Found {len(old_files)} old data files (not from {current_prefix}):")
    for i, file in enumerate(old_files[:10]):  # Show first 10
        print(f"  - {file}")
    if len(old_files) > 10:
        print(f"  ... and {len(old_files) - 10} more files")
    
    # Ask for confirmation
    choice = input(f"\nDo you want to delete these {len(old_files)} old files? [y/N]: ").strip().lower()
    
    if choice in ['y', 'yes']:
        deleted_count = 0
        for file in old_files:
            try:
                os.remove(os.path.join(stats_dir, file))
                deleted_count += 1
            except OSError as e:
                print(f"Error deleting {file}: {e}")
        print(f"Successfully deleted {deleted_count} old data files.")
    else:
        print("Deletion cancelled.")

def updateMetagames():
    """Update metagames data for the previous month"""
    current_prefix = get_current_month_prefix()
    year, month = current_prefix.split('-')
    
    urls = [
        f'https://www.smogon.com/stats/{year}-{month}/chaos/',
        f'https://www.smogon.com/stats/{year}-{month}-DLC1/chaos/',
        f'https://www.smogon.com/stats/{year}-{month}-DLC2/chaos/',
        f'https://www.smogon.com/stats/{year}-{month}-H1/chaos/',
        f'https://www.smogon.com/stats/{year}-{month}-H2/chaos/',
    ]
    
    for url in urls:
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                print(f"Getting stats from {url}")
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link['href']
                    if ".json" in href and ".gz" not in href:
                        filename = f'stats/{year}-{month}-{href}'
                        
                        if os.path.exists(filename):
                            print(f"File {filename} already exists, skipping download.")
                            continue
                        
                        print(f"Downloading {href}...")
                        try:
                            file_response = requests.get(url + href, timeout=30)
                            file_response.raise_for_status()
                            
                            os.makedirs('stats', exist_ok=True)
                            with open(filename, 'w', encoding="utf-8") as file:
                                file.write(file_response.text)
                        except requests.RequestException as e:
                            print(f"Error downloading {href}: {e}")
            else:
                print(f"Unable to access {url} (Status: {response.status_code})")
        except requests.RequestException as e:
            print(f"Error accessing {url}: {e}")

def extract_battle_icon_indexes_from_url(mjs_url, output_json_path):
    """Extract battle icon indexes from MJS URL and save to JSON"""
    try:
        response = requests.get(mjs_url, timeout=30)
        response.raise_for_status()
        mjs_content = response.text.splitlines()

        # Extract the content of BattlePokemonIconIndexes
        start_index = mjs_content.index('const BattlePokemonIconIndexes = {')
        end_index = start_index
        while mjs_content[end_index] != '};':
            end_index += 1
        icon_indexes_content = mjs_content[start_index + 1:end_index]

        # Clean and process the content
        cleaned_content = [line for line in icon_indexes_content if not line.strip().startswith('//')]
        content_string = ''.join(cleaned_content)
        content_string = re.sub(r'/\*.*?\*/', '', content_string, flags=re.DOTALL)
        content_string = re.sub(r'(\d+ \+ \d+)', lambda x: str(eval(x.group(1))), content_string)
        content_string = re.sub(r'(\w+):', r'"\1":', content_string)

        # Convert to dictionary and save
        icon_indexes_dict = eval(f"{{{content_string}}}")
        
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, 'wb') as json_file:
            pyjson5.dump(icon_indexes_dict, json_file, indent=4)
            
    except (requests.RequestException, ValueError, IndexError) as e:
        print(f"Error extracting icon indexes: {e}")

def updateData():
    """Update Pokemon data (pokedex and forms)"""
    print("Getting pokedex data.")
    try:
        url = 'https://play.pokemonshowdown.com/data/pokedex.json'
        filename = 'stats/pokedex.json'
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        os.makedirs('stats', exist_ok=True)
        with open(filename, 'w', encoding="utf-8") as file:
            file.write(response.text)
    except requests.RequestException as e:
        print(f"Error getting pokedex data: {e}")
        return
    
    print("Getting form data.")
    url = 'https://raw.githubusercontent.com/smogon/sprites/master/ps-pokemon.sheet.mjs'
    filename = 'stats/forms_index.json'
    
    extract_battle_icon_indexes_from_url(url, filename)

def updateImage():
    """Update Pokemon icon sheet image"""
    print("Getting images.")
    try:
        url = 'https://play.pokemonshowdown.com/sprites/pokemonicons-sheet.png'
        filename = 'pokemonicons-sheet.png'
        
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    except requests.RequestException as e:
        print(f"Error downloading image: {e}")

def extract_gen(s):
    """Extract the generation number from the string."""
    val = s.split("gen")[1].split("1v1")[0].split("2v2")[0].split("350")[0]
    val = int(re.findall(r'\d+', val)[0]) if re.findall(r'\d+', val) else None
    return str(val)

def generateFormatList():
    """Generate format list mapping from Smogon data"""
    try:
        response = requests.get('https://raw.githubusercontent.com/smogon/pokemon-showdown/master/config/formats.ts', timeout=30)
        response.raise_for_status()
        mjs_content = response.text

        format_names = re.findall(r"name:\s*['\"]([^'\"]+)['\"]", mjs_content)

        if not os.path.exists("stats"):
            print("Stats directory not found, skipping format list generation.")
            return
            
        meta_games_list = ["stats/" + f for f in os.listdir("stats/") if f.split("-")[-1] == "0.json"]
        meta_games_list = [f.split("-")[-2] for f in meta_games_list]
        
        meta_names = {}
        for meta in meta_games_list:
            word = meta
            possibilities = format_names
            normalized_possibilities = {p.lower(): p for p in possibilities}
            result = difflib.get_close_matches(word, normalized_possibilities.keys(), 10)
            normalized_result = [normalized_possibilities[r] for r in result]
            
            if normalized_result:
                close = normalized_result[0]
                pokeSearch = close

                if re.sub(r'[^a-z0-9]+', '', pokeSearch.lower()) != meta:
                    print(f"Possible incorrect name with {meta} as {pokeSearch}")

                meta_names[meta] = pokeSearch
            else:
                print(f"Unable to find format name for {meta}")
        
        filename = 'stats/meta_names.json'
        os.makedirs('stats', exist_ok=True)
        with open(filename, 'wb') as file:
            pyjson5.dump(meta_names, file)
            
    except requests.RequestException as e:
        print(f"Error generating format list: {e}")

def main():
    """Main function to run all update tasks"""
    print("Starting Pokemon data update...")
    print(f"Current month prefix: {get_current_month_prefix()}")
    
    # Ask about cleaning old data
    clean_old_data()
    
    # Update all data
    updateData()
    updateImage()
    updateMetagames()
    generateFormatList()
    
    print("Update completed successfully!")

if __name__ == "__main__":
    main()