import os
import json
import csv
import random
from typing import Dict, List, Set, Tuple

# Resolve paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "data/family_trees_json")
OUTPUT_DIR_1 = os.path.join(SCRIPT_DIR, "test_cases/1")
OUTPUT_DIR_2 = os.path.join(SCRIPT_DIR, "test_cases/2")

RELATIONSHIPS = [
    "CHILD", "PARENT", "SPOUSE", "SIBLING", "GRANDCHILD", "GRANDPARENT",
    "UNCLE_OR_AUNT", "NEPHEW_OR_NIECE", "GREAT_GRANDCHILD",
    "GREAT_GRANDPARENT", "COUSIN"
]

def load_json(filepath: str) -> Dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_graph(data: Dict):
    """
    Builds a graph representation of the family tree.
    Returns:
        nodes: Set of all person names.
        parent_map: Dict[child, Set[parents]] - though usually tree has 1 parent in this format, 
                    conceptually valid to have set.
        children_map: Dict[parent, Set[children]]
        spouse_map: Dict[person, spouse]
    """
    nodes = set()
    parent_map: Dict[str, Set[str]] = {}
    children_map: Dict[str, Set[str]] = {}
    spouse_map: Dict[str, str] = {}

    def traverse(node):
        name = node["name"]
        nodes.add(name)
        
        # Handle spouse
        if "spouse" in node and node["spouse"]:
            spouse = node["spouse"]
            nodes.add(spouse)
            spouse_map[name] = spouse
            spouse_map[spouse] = name
            
            # In this tree format, children belong to the "main" node. 
            # Implied they are children of the spouse too in a biological sense for this exercise.
            # We will link children to BOTH parents if a spouse exists.
        
        children = node.get("children", [])
        current_parents = {name}
        if name in spouse_map:
            current_parents.add(spouse_map[name])
            
        if name not in children_map:
            children_map[name] = set()
        if name in spouse_map and spouse_map[name] not in children_map:
             children_map[spouse_map[name]] = set()

        for child in children:
            child_name = child["name"]
            
            # Parent -> Child
            children_map[name].add(child_name)
            if name in spouse_map:
                children_map[spouse_map[name]].add(child_name)
            
            # Child -> Parent
            if child_name not in parent_map:
                parent_map[child_name] = set()
            parent_map[child_name].add(name)
            if name in spouse_map:
                parent_map[child_name].add(spouse_map[name])

            traverse(child)

    traverse(data)
    return nodes, parent_map, children_map, spouse_map

def find_relationships(nodes, parent_map, children_map, spouse_map):
    rels = {rel: [] for rel in RELATIONSHIPS}
    
    # Pre-compute useful lookups
    def get_parents(p): return parent_map.get(p, set())
    def get_children(p): return children_map.get(p, set())
    def get_spouse(p): return spouse_map.get(p)
    
    for person in nodes:
        parents = get_parents(person)
        children = get_children(person)
        spouse = get_spouse(person)
        
        # SPOUSE
        if spouse:
            # Avoid duplicates by string comparison
            if person < spouse:
                rels["SPOUSE"].append((person, spouse))
                rels["SPOUSE"].append((spouse, person))
        
        # PARENT / CHILD
        for kid in children:
            rels["PARENT"].append((person, kid))
            rels["CHILD"].append((kid, person))
            
        # SIBLING
        # Share at least one parent
        if parents:
            # Get all potential siblings from all parents
            siblings = set()
            for parent in parents:
                siblings.update(get_children(parent))
            siblings.discard(person) # Remove self
            for sib in siblings:
                rels["SIBLING"].append((person, sib))
        
        # GRANDPARENT / GRANDCHILD
        # Parents' parents
        grandparents = set()
        for parent in parents:
            grandparents.update(get_parents(parent))
        for gp in grandparents:
            rels["GRANDCHILD"].append((person, gp))
            rels["GRANDPARENT"].append((gp, person))

        # GREAT_GRANDPARENT / GREAT_GRANDCHILD
        # Grandparents' parents
        great_grandparents = set()
        for gp in grandparents:
            great_grandparents.update(get_parents(gp))
        for ggp in great_grandparents:
            rels["GREAT_GRANDCHILD"].append((person, ggp))
            rels["GREAT_GRANDPARENT"].append((ggp, person))
            
        # UNCLE_OR_AUNT / NEPHEW_OR_NIECE
        # Parent's siblings
        uncles_aunts = set()
        for parent in parents:
            # Parents siblings
            p_parents = get_parents(parent)
            for pp in p_parents:
                p_siblings = get_children(pp)
                p_siblings.discard(parent)
                uncles_aunts.update(p_siblings)
                
                # Should we include spouses of uncles/aunts? Usually "Uncle" includes Uncle by marriage.
                # Requirement just says UNCLE_OR_AUNT. Let's include blood relatives for simplicity first, 
                # but valid interpretation often includes spouses.
                # Given the strict "family tree" generation, sticking to blood relations + direct spouses is safer logic?
                # Actually, standard definition usually includes spouses. Let's add spouses of parents' siblings.
                
                # Copy set to iterate
                current_blood_uncles = list(p_siblings)
                for u in current_blood_uncles:
                    u_spouse = get_spouse(u)
                    if u_spouse:
                        uncles_aunts.add(u_spouse)

        for ua in uncles_aunts:
            rels["NEPHEW_OR_NIECE"].append((person, ua))
            rels["UNCLE_OR_AUNT"].append((ua, person))
            
        # COUSIN
        # Children of Uncles/Aunts (specifically blood uncles/aunts)
        # Or: Children of parents' siblings
        # Logic: My parent -> Their sibling -> Their child
        cousins = set()
        for parent in parents:
            p_parents = get_parents(parent) # Grandparents
            for gp in p_parents:
                gp_children = get_children(gp) # Aunts/Uncles (including parent)
                for p_sibling in gp_children:
                    if p_sibling == parent: continue
                    
                    p_sibling_children = get_children(p_sibling)
                    cousins.update(p_sibling_children)
        
        for coz in cousins:
            rels["COUSIN"].append((person, coz))

    # De-duplicate lists (since we iterate over every person, pair (A,B) might be added when processing A and again when processing B? 
    # Actually for "SPOUSE", I handled it.
    # For "SIBLING", I do person -> sib. When loop reaches sib, it does sib -> person. Valid.
    # For unidirectional like "PARENT", person -> kid. Loop reaches kid, doesn't add kid -> person to PARENT list. Valid.
    # For "COUSIN", person -> coz. Loop reaches coz, does coz -> person. Valid.
    
    # However, we might add the same pair multiple times if multiple paths exist?
    # E.g. Siblings share 2 parents. For 'person', we iterate parent1 -> adds sib. parent2 -> adds sib.
    # So we need to deduplicate.
    for k in rels:
        rels[k] = list(set(rels[k]))
        
    return rels

def process_file(filename):
    input_path = os.path.join(INPUT_DIR, filename)
    data = load_json(input_path)
    nodes, parent_map, children_map, spouse_map = build_graph(data)
    all_rels = find_relationships(nodes, parent_map, children_map, spouse_map)
    
    output_rows = []
    
    for rel_type in RELATIONSHIPS:
        pairs = all_rels[rel_type]
        if not pairs:
            continue
            
        # Select 1 random pairs
        selected = random.sample(pairs, min(len(pairs), 1))
        for p1, p2 in selected:
            output_rows.append([p1, p2, rel_type])
            
    # Write to CSV
    csv_filename = os.path.splitext(filename)[0] + ".csv"
    output_path = os.path.join(OUTPUT_DIR_1, csv_filename)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["person_a", "person_b", "relationship_type"])
        writer.writerows(output_rows)
    print(f"Processed {filename} -> {output_path}")

    # --- New Logic for test_cases_2 ---
    if not os.path.exists(OUTPUT_DIR_2):
        os.makedirs(OUTPUT_DIR_2)

    test_cases_2_data = []
    processed_queries = set()  # To avoid duplicate questions for the same person_b + relationship

    for row in output_rows:
        # row is [person_a, person_b, rel_type]
        p_b = row[1]
        r_type = row[2]
        
        # Unique identifier for the question
        query_key = (p_b, r_type)
        if query_key in processed_queries:
            continue
        processed_queries.add(query_key)

        # Find ALL person_a that satisfy Relationship(person_a, p_b) == r_type
        # We look into all_rels[r_type] for pairs (p1, p2) where p2 == p_b
        possible_a = [p1 for (p1, p2) in all_rels[r_type] if p2 == p_b]
        
        test_cases_2_data.append({
            "person_b": p_b,
            "relationship_type": r_type,
            "possible_person_a": sorted(possible_a) # Sort for consistent order
        })
    
    # Write to JSON in test_cases_2
    json_filename = os.path.splitext(filename)[0] + ".json"
    output_path_2 = os.path.join(OUTPUT_DIR_2, json_filename)
    
    with open(output_path_2, 'w', encoding='utf-8') as f:
        json.dump(test_cases_2_data, f, ensure_ascii=False, indent=2)
    print(f"Generated test cases 2 for {filename} -> {output_path_2}")

def main():
    if not os.path.exists(OUTPUT_DIR_1):
        os.makedirs(OUTPUT_DIR_1)
    if not os.path.exists(OUTPUT_DIR_2):
        os.makedirs(OUTPUT_DIR_2)
        
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.json')]
    print(f"Found {len(files)} JSON files.")
    
    for f in files:
        process_file(f)

if __name__ == "__main__":
    main()
