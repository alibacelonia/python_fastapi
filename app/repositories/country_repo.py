import os
import json

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.country_ids = []

def insert_into_trie(root, word, country_id):
    node = root
    for char in word:
        if char not in node.children:
            node.children[char] = TrieNode()
        node = node.children[char]
        node.country_ids.append(country_id)
    node.is_end_of_word = True

def search_prefix_in_trie(root, prefix):
    node = root
    for char in prefix:
        if char not in node.children:
            return []
        node = node.children[char]
    return node.country_ids

def create_trie_index(data):
    root = TrieNode()

    for country in data:
        country_id = country['id']
        country_name = country['name']
        insert_into_trie(root, country_name, country_id)

    return root

def create_id_index(data):
    id_index = {}
    for country in data:
        country_id = country['id']
        id_index[country_id] = country
    return id_index

file_path = os.path.join("app", "files", "countries.json")
with open(file_path) as json_file:
    data = json.load(json_file)

# Create the Trie Index
trie_index = create_trie_index(data)

id_index = create_id_index(data)

def get_all_countries():
    return data

def search_country(search_query: str):
    # Search for a country by name
    # search_query = "Afghanistan"
    matching_country_ids = search_prefix_in_trie(trie_index, search_query.capitalize())
    matching_countries = [country for country in data if country['id'] in matching_country_ids]
    return matching_countries

def get_country_by_id(search_id: int):
    matching_country = id_index.get(search_id)

    if matching_country:
        return matching_country
    else:
        return {"status_code": 404, "detail": "Country not found."}