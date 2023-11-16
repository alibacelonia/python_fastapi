import os
import json

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.state_ids = []

def insert_into_trie(root, word, state_id):
    node = root
    for char in word:
        if char not in node.children:
            node.children[char] = TrieNode()
        node = node.children[char]
        node.state_ids.append(state_id)
    node.is_end_of_word = True

def search_prefix_in_trie(root, prefix):
    node = root
    for char in prefix:
        if char not in node.children:
            return []
        node = node.children[char]
    return node.state_ids

def create_trie_index(data):
    root = TrieNode()

    for state in data:
        state_id = state['id']
        state_name = state['name']
        insert_into_trie(root, state_name, state_id)

    return root

def create_id_index(data):
    id_index = {}
    for state in data:
        state_id = state['id']
        id_index[state_id] = state
    return id_index

def create_country_code_index(data):
    id_index = {}
    for record in data:
        country_code = record.get('country_code')
        if country_code not in id_index:
            id_index[country_code] = []
        id_index[country_code].append(record)
    return id_index

def filter_by_country_code(index, target_country_code):
    return index.get(target_country_code, [])

file_path = os.path.join("app", "files", "states.json")
with open(file_path) as json_file:
    data = json.load(json_file)

# Create the Trie Index
trie_index = create_trie_index(data)

id_index = create_id_index(data)

# Create the Index for country_id
country_id_index = create_country_code_index(data)

def get_all_states():
    return data

def search_state(search_query: str):
    # Search for a state by name
    # search_query = "Afghanistan"
    matching_state_ids = search_prefix_in_trie(trie_index, search_query.capitalize())
    matching_states = [state for state in data if state['id'] in matching_state_ids]
    return matching_states

def get_state_by_id(search_id: int):
    matching_state = id_index.get(search_id)

    if matching_state:
        return matching_state
    else:
        return {"status_code": 404, "detail": "State not found."}
    
def get_state_by_country_code(target_country_code:str):

    # Apply the filter using the index
    filtered_records = filter_by_country_code(country_id_index, target_country_code)

    if filtered_records:
        return filtered_records
    else:
        return {"status_code": 404, "detail": "State not found."}