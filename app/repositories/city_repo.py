import os
import json

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.city_ids = []

def insert_into_trie(root, word, city_id):
    node = root
    for char in word:
        if char not in node.children:
            node.children[char] = TrieNode()
        node = node.children[char]
        node.city_ids.append(city_id)
    node.is_end_of_word = True

def search_prefix_in_trie(root, prefix):
    node = root
    for char in prefix:
        if char not in node.children:
            return []
        node = node.children[char]
    return node.city_ids

def create_trie_index(data):
    root = TrieNode()

    for city in data:
        city_id = city['id']
        city_name = city['name']
        insert_into_trie(root, city_name, city_id)

    return root

def create_id_index(data):
    id_index = {}
    for city in data:
        city_id = city['id']
        id_index[city_id] = city
    return id_index

def create_country_code_index(data):
    id_index = {}
    for record in data:
        country_code = record.get('country_code')
        if country_code not in id_index:
            id_index[country_code] = []
        id_index[country_code].append(record)
    return id_index

def create_state_code_index(data):
    id_index = {}
    for record in data:
        state_code = record.get('state_code')
        if state_code not in id_index:
            id_index[state_code] = []
        id_index[state_code].append(record)
    return id_index

def filter_by_code(index, target_code):
    return index.get(target_code, [])

file_path = os.path.join("app", "files", "cities.json")
with open(file_path) as json_file:
    data = json.load(json_file)

# Create the Trie Index
trie_index = create_trie_index(data)

id_index = create_id_index(data)

# Create the Index for country_id
country_id_index = create_country_code_index(data)
state_id_index = create_state_code_index(data)

def get_all_cities():
    return data

def search_city(search_query: str):
    # Search for a city by name
    # search_query = "Afghanistan"
    matching_city_ids = search_prefix_in_trie(trie_index, search_query.capitalize())
    matching_cities = [city for city in data if city['id'] in matching_city_ids]
    return matching_cities

def get_city_by_id(search_id: int):
    matching_city = id_index.get(search_id)

    if matching_city:
        return matching_city
    else:
        return {"status_code": 404, "detail": "City not found."}
    
def get_city_by_country_code(target_country_code:str):

    # Apply the filter using the index
    filtered_records = filter_by_code(country_id_index, target_country_code)

    if filtered_records:
        return filtered_records
    else:
        return {"status_code": 404, "detail": "State not found."}  
    
def get_city_by_state_code(target_country_code:str):

    # Apply the filter using the index
    filtered_records = filter_by_code(state_id_index, target_country_code)

    if filtered_records:
        return filtered_records
    else:
        return {"status_code": 404, "detail": "City not found."}  
    