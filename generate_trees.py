import json
import random
import os
import shutil

OUTPUT_DIR = "data/family_trees_json"
TARGET_GENERATIONS = [4, 5, 6, 7]
TARGET_NODES = [3, 4, 5, 6, 7]


NAMELIST_RAW = """
清風
安寧
夢瑤
子輝
子瑜
子涵
文莉
安邦
子晨
立民
雅文
子濤
子賢
富強
和睦
子琪
永祿
興業
明珠
思源
子謙
長樂
永安
明達
雅靜
文傑
愛玲
文靜
思齊
柏林
子睿
興隆
興華
子墨
明賢
武雄
子陽
思遠
靜宜
美慧
子悅
長福
興盛
和平
文秀
安民
德康
子軒
和光
安國
子豪
長青
文雅
秀英
子霖
柏森
瑞雪
和悅
明正
玉蘭
明智
永芳
子辰
明月
夢潔
安康
和順
麗華
建國
思賢
興邦
天朗
慧敏
永福
曉晴
星辰
雅麗
和順
和光
"""
NAMES = [n.strip() for n in NAMELIST_RAW.strip().split('\n') if n.strip()]

class Node:
    def __init__(self, name_idx, generation):
        self.name_idx = name_idx # Index in shared name list to assign unique names later
        self.generation = generation # 1-based generation
        self.children = []
        self.spouse = None

    def add_child(self, child):
        self.children.append(child)

    def to_dict(self, name_map):
        d = {
            "name": name_map[self.name_idx],
            "children": [child.to_dict(name_map) for child in self.children]
        }
        if self.spouse:
            d["spouse"] = self.spouse
        return d
    
    def get_max_depth(self):
        if not self.children:
            return self.generation
        return max(child.get_max_depth() for child in self.children)

    def count_nodes(self):
        return 1 + sum(child.count_nodes() for child in self.children)

def generate_tree(target_generations, target_nodes):
    """
    Generates a tree satisfying the constraints.
    Returns the root Node object.
    """
    
    # We need unique identifiers for nodes during construction to manage names later
    
    root = Node(0, 1)
    nodes_created = 1
    current_nodes = [root]

    # Distinct Sets to track branch constraints
    # We'll use a dictionary to track "allowed_max_depth" for each node
    # Root is always allowed up to target_generations
    node_depth_limits = {root: target_generations}

    # --- Step 1: Guarantee Max Depth (Main Branch) ---
    # We must have at least one branch reaching `target_generations`.
    
    current_deep_node = root
    for g in range(2, target_generations + 1):
        # Create a child for the current deep node
        new_node = Node(nodes_created, g)
        current_deep_node.add_child(new_node)
        current_nodes.append(new_node)
        node_depth_limits[new_node] = target_generations # Main branch can go to max
        current_deep_node = new_node
        nodes_created += 1

    # --- Step 2: Asymmetry Constraint ---
    # "At least one other major branch that ends 1 to 2 generations earlier"
    
    asymmetry_target_depth = max(2, target_generations - random.choice([1, 2]))
    
    # Check budget
    nodes_needed_for_branch = asymmetry_target_depth - 1
    
    if nodes_created < target_nodes and nodes_needed_for_branch > 0:
         # Constraint check: Do we have enough nodes left?
         # We need to fill `nodes_needed_for_branch` nodes.
         # AND we might need more to fill `target_nodes`.
         if (target_nodes - nodes_created) >= nodes_needed_for_branch:
            # Create second branch from root
            current_branch_node = root
            for g in range(2, asymmetry_target_depth + 1):
                new_node = Node(nodes_created, g)
                current_branch_node.add_child(new_node)
                current_nodes.append(new_node)
                node_depth_limits[new_node] = asymmetry_target_depth # Limit this branch
                current_branch_node = new_node
                nodes_created += 1

    # --- Step 3: Fill Remaining Nodes ---
    
    while nodes_created < target_nodes:
        # Pick a random candidate parent
        # Valid candidate: Node where (node.generation + 1) <= ITS LIMIT
        candidates = [n for n in current_nodes if (n.generation + 1) <= node_depth_limits.get(n, target_generations)]
        
        if not candidates:
            break
            
        parent = random.choice(candidates)
        new_node = Node(nodes_created, parent.generation + 1)
        parent.add_child(new_node)
        current_nodes.append(new_node)
        
        # Inherit limit from parent
        node_depth_limits[new_node] = node_depth_limits.get(parent, target_generations)
        
        nodes_created += 1

    # --- Step 4: Assign Names ---
    # Shuffle names and assign
    available_names = NAMES[:]
    random.shuffle(available_names)
    
    # Map node indices to names
    if len(available_names) < target_nodes:
        multiplier = (target_nodes // len(available_names)) + 1
        available_names = available_names * multiplier
    
    final_names = available_names[:target_nodes]
    name_map = {i: name for i, name in enumerate(final_names)}
    
    # --- Step 5: Assign Spouses ---
    remaining_names = available_names[target_nodes:]
    
    for node in current_nodes:
        if not remaining_names:
            break
            
        # Decision: Give spouse?
        # Higher chance if node has children (looks like a geometric family unit)
        has_children = len(node.children) > 0
        probability = 0.7 if has_children else 0.2
        
        if random.random() < probability:
            spouse_name = remaining_names.pop()
            node.spouse = spouse_name

    # --- Step 6: Randomize Children Order ---
    # To avoid the "Main Branch" always being the first child
    for node in current_nodes:
        if node.children:
            random.shuffle(node.children)

    return root, name_map

def verify_tree(root, target_nodes, target_generations):
    """
    Internal verification.
    """
    actual_depth = root.get_max_depth()
    actual_nodes = root.count_nodes()
    
    depth_ok = (actual_depth == target_generations)
    nodes_ok = (actual_nodes == target_nodes)
    
    # Asymmetry Check
    asymmetry_ok = False
    
    if len(root.children) >= 2:
        child_depths = [c.get_max_depth() for c in root.children]
        max_child_depth = max(child_depths)
        
        if max_child_depth == target_generations:
            child_depths.remove(target_generations)
            for d in child_depths:
                diff = target_generations - d
                if 1 <= diff <= 2:
                    asymmetry_ok = True
                    break
                    
    # Relax asymmetry if node count is very tight
    # Min nodes for strict asymmetry = (G) + (G-2) = 2G - 2
    if target_nodes < (2 * target_generations - 2):
        # Allow pass if we at least hit depth and node count, 
        # acknowledging we might not have budget for a full second major branch
        if depth_ok and nodes_ok:
             return True, f"D:{actual_depth} N:{actual_nodes} A:Skipped(LowNodes)"

    return depth_ok and nodes_ok and asymmetry_ok, f"D:{actual_depth}/{target_generations} N:{actual_nodes}/{target_nodes} A:{asymmetry_ok}"

def main():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    print("Generating trees with pure Python rules...")
    
    for g in TARGET_GENERATIONS:
        for n_multiplier in TARGET_NODES:
            total_nodes = g * n_multiplier
            
            for edition in range(1, 4):
                filename = f"G{g}_N{total_nodes}_{edition}.json"
                
                print(f"Generating {filename} (Gen: {g}, Nodes: {total_nodes}, Edition: {edition})...")
                
                # RETRY LOOP
                max_retries = 20
                success = False
                
                for attempt in range(max_retries):
                    root, name_map = generate_tree(g, total_nodes)
                    is_valid, stats = verify_tree(root, total_nodes, g)
                    
                    if is_valid:
                        tree_dict = root.to_dict(name_map)
                        with open(os.path.join(OUTPUT_DIR, filename), 'w', encoding='utf-8') as f:
                            json.dump(tree_dict, f, ensure_ascii=False, indent=2)
                        print(f"  -> SUCCESS (Attempt {attempt+1}): {stats}")
                        success = True
                        break
                
                if not success:
                    print(f"  -> FAILED after {max_retries} attempts. Last stats: {stats}")
                    # Save the last one anyway for debugging
                    tree_dict = root.to_dict(name_map)
                    with open(os.path.join(OUTPUT_DIR, filename), 'w', encoding='utf-8') as f:
                        json.dump(tree_dict, f, ensure_ascii=False, indent=2)


    print(f"\nDone. Files saved to {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
