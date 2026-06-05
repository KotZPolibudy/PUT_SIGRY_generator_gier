import os
import sys
import json
import argparse
import urllib.request
import urllib.error
from strips_planner import Domain, Problem, solve_pddl, parse_pddl_text, parse_typed_list

def check_ollama(url):
    try:
        req = urllib.request.Request(f"{url}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            return [m["name"] for m in data.get("models", [])]
    except Exception as e:
        print(f"Warning: Cannot connect to Ollama at {url}: {e}")
        return None

def call_ollama(prompt, model, url, system_prompt=None):
    headers = {"Content-Type": "application/json"}
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "format": "json"
    }
    
    req = urllib.request.Request(
        f"{url}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["message"]["content"]
    except urllib.error.URLError as e:
        print(f"HTTP Error calling Ollama: {e.reason}")
        return None
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return None

def slugify(text):
    import re
    text = text.lower()
    pl_chars = str.maketrans("ąęćłńóśźż", "aeclnoszz")
    text = text.translate(pl_chars)
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')

def get_campaign_slug(prompt):
    slug = slugify(prompt)
    parts = slug.split('_')
    if len(parts) > 6:
        slug = '_'.join(parts[:6])
    return slug

def auto_repair_pddl(pddl_text, quest_data, domain):
    def flatten_nested_symbols(expr):
        if isinstance(expr, list):
            if len(expr) == 1 and isinstance(expr[0], str):
                return expr[0]
            return [flatten_nested_symbols(x) for x in expr]
        return expr

    # Resolve player name
    player_name = "hero"
    if "characters" in quest_data:
        for c_id, c_info in quest_data["characters"].items():
            if c_id in ["hero", "player", "biographer"] or "player" in c_info.get("description", "").lower() or "biographer" in c_info.get("description", "").lower():
                player_name = c_id
                break

    def fix_malformed_predicates(expr, p_name):
        if isinstance(expr, list):
            if not expr:
                return expr
            new_expr = []
            for x in expr:
                new_expr.append(fix_malformed_predicates(x, p_name))
            
            pred = new_expr[0]
            if isinstance(pred, str):
                # Standardize invented predicate names
                if pred in ['has-hero', 'has-player', 'has_hero', 'has_player']:
                    pred = 'has'
                    new_expr[0] = 'has'
                elif pred in ['at-hero', 'at-player', 'at_hero', 'at_player']:
                    pred = 'at'
                    new_expr[0] = 'at'
                    
                if pred == 'has':
                    if len(new_expr) == 2:
                        return ['has', p_name, new_expr[1]]
                    elif len(new_expr) > 3:
                        return ['has', new_expr[1], new_expr[-1]]
                elif pred == 'at':
                    if len(new_expr) == 2:
                        return ['at', p_name, new_expr[1]]
                    elif len(new_expr) > 3:
                        return ['at', new_expr[1], new_expr[-1]]
                elif pred == 'key-for':
                    if len(new_expr) > 3:
                        return ['key-for', new_expr[1], new_expr[-1]]
                elif pred == 'item-at':
                    if len(new_expr) > 3:
                        return ['item-at', new_expr[1], new_expr[-1]]
                elif pred == 'connected':
                    if len(new_expr) > 3:
                        return ['connected', new_expr[1], new_expr[-1]]
            return new_expr
        return expr

    try:
        tree = parse_pddl_text(pddl_text)
        if not tree or tree[0] != 'define':
            return pddl_text
            
        tree = flatten_nested_symbols(tree)
        tree = fix_malformed_predicates(tree, player_name)
            
        # Find :objects block
        objects_idx = -1
        for idx, item in enumerate(tree):
            if isinstance(item, list) and item[0] == ':objects':
                objects_idx = idx
                break
                
        if objects_idx == -1:
            # Create :objects block if it doesn't exist
            tree.insert(2, [':objects'])
            objects_idx = 2
            
        objects_item = tree[objects_idx]
        parsed_objs = parse_typed_list(objects_item[1:])
        
        # Clean character -> npc/player and refine types from JSON
        fixed_objs = []
        for obj, otype in parsed_objs:
            if otype in ["character", "object"]:
                refined_type = None
                if "locations" in quest_data and obj in quest_data["locations"]:
                    refined_type = "location"
                elif "items" in quest_data and obj in quest_data["items"]:
                    refined_type = "item"
                elif "characters" in quest_data and obj in quest_data["characters"]:
                    char_info = quest_data["characters"][obj]
                    if obj in ["hero", "player", "biographer"] or "player" in char_info.get("description", "").lower() or "biographer" in char_info.get("description", "").lower():
                        refined_type = "player"
                    else:
                        refined_type = "npc"
                
                if refined_type:
                    fixed_objs.append((obj, refined_type))
                else:
                    if otype == "character":
                        fixed_objs.append((obj, "npc"))
                    else:
                        fixed_objs.append((obj, otype))
            else:
                fixed_objs.append((obj, otype))
                
        declared_objs = {obj for obj, _ in fixed_objs}
        
        # Collect referenced objects from init and goal
        init_item = None
        goal_item = None
        for item in tree[1:]:
            if isinstance(item, list):
                if item[0] == ':init':
                    init_item = item
                elif item[0] == ':goal':
                    goal_item = item
                    
        referenced = set()
        def collect_terms(expr):
            if isinstance(expr, list):
                if expr[0] in ['and', 'not']:
                    for sub in expr[1:]:
                        collect_terms(sub)
                else:
                    for term in expr[1:]:
                        if isinstance(term, str) and not term.startswith('?'):
                            referenced.add(term)
                            
        if init_item:
            for fact in init_item[1:]:
                collect_terms(fact)
        if goal_item:
            collect_terms(goal_item[1])
            
        undeclared = referenced - declared_objs
        
        new_objects_by_type = {}
        for obj in undeclared:
            obj_type = None
            # 1. JSON check
            if "locations" in quest_data and obj in quest_data["locations"]:
                obj_type = "location"
            elif "items" in quest_data and obj in quest_data["items"]:
                obj_type = "item"
            elif "characters" in quest_data and obj in quest_data["characters"]:
                char_info = quest_data["characters"][obj]
                if obj in ["hero", "player", "biographer"] or "player" in char_info.get("description", "").lower() or "biographer" in char_info.get("description", "").lower():
                    obj_type = "player"
                else:
                    obj_type = "npc"
                    
            # 2. Predicate check
            if not obj_type:
                def infer_type_from_facts(expr):
                    if isinstance(expr, list):
                        if expr[0] in ['and', 'not']:
                            for sub in expr[1:]:
                                res = infer_type_from_facts(sub)
                                if res: return res
                        else:
                            pred = expr[0]
                            if pred in domain.predicates:
                                parsed_sig = parse_typed_list(domain.predicates[pred])
                                for idx, term in enumerate(expr[1:]):
                                    if term == obj and idx < len(parsed_sig):
                                        return parsed_sig[idx][1]
                    return None
                if init_item:
                    for fact in init_item[1:]:
                        obj_type = infer_type_from_facts(fact)
                        if obj_type: break
                if not obj_type and goal_item:
                    obj_type = infer_type_from_facts(goal_item[1])
                    
            if not obj_type:
                obj_type = "object"
            if obj_type == "character":
                obj_type = "npc"
                
            if obj_type not in new_objects_by_type:
                new_objects_by_type[obj_type] = []
            new_objects_by_type[obj_type].append(obj)
            
        # Re-build the :objects block
        new_objects_list = [':objects']
        for obj, otype in fixed_objs:
            new_objects_list.append(obj)
            new_objects_list.append('-')
            new_objects_list.append(otype)
            
        for otype, objs in new_objects_by_type.items():
            for obj in objs:
                new_objects_list.append(obj)
            new_objects_list.append('-')
            new_objects_list.append(otype)
            
        tree[objects_idx] = new_objects_list

        # --- Automatic Init State Additions ---
        if init_item:
            # 1. Ensure all declared characters are marked as is-alive
            characters = []
            for obj, otype in fixed_objs:
                if otype in ["player", "npc"]:
                    characters.append(obj)
            for otype, objs in new_objects_by_type.items():
                if otype in ["player", "npc"]:
                    characters.extend(objs)
            
            alive_chars = set()
            for fact in init_item[1:]:
                if isinstance(fact, list) and fact[0] == 'is-alive' and len(fact) == 2:
                    alive_chars.add(fact[1])
            
            for char in characters:
                if char not in alive_chars:
                    init_item.append(['is-alive', char])

            # 2. Ensure connections are bidirectional
            conns = set()
            for fact in init_item[1:]:
                if isinstance(fact, list) and fact[0] == 'connected' and len(fact) == 3:
                    conns.add((fact[1], fact[2]))
            
            for u, v in list(conns):
                if (v, u) not in conns:
                    init_item.append(['connected', v, u])
                    conns.add((v, u))

            # 3. Ensure player has a starting location
            has_at = False
            for fact in init_item[1:]:
                if isinstance(fact, list) and fact[0] == 'at' and len(fact) == 3 and fact[1] == player_name:
                    has_at = True
                    break
            if not has_at:
                locs = []
                for obj, otype in fixed_objs:
                    if otype == "location":
                        locs.append(obj)
                for otype, objs in new_objects_by_type.items():
                    if otype == "location":
                        locs.extend(objs)
                if locs:
                    init_item.append(['at', player_name, locs[0]])
        
        # Serialize back
        def serialize(t):
            if isinstance(t, list):
                return "(" + " ".join(serialize(x) for x in t) + ")"
            return str(t)
            
        return serialize(tree)
    except Exception as e:
        print(f"Warning: Auto-repair failed: {e}")
        return pddl_text

def diagnose_pddl_problem(problem, domain, quest_data=None):
    warnings = []
    
    players = [obj for obj, otype in problem.objects.items() if otype == 'player']
    npcs = [obj for obj, otype in problem.objects.items() if otype == 'npc']
    locations = [obj for obj, otype in problem.objects.items() if otype == 'location']
    items = [obj for obj, otype in problem.objects.items() if otype == 'item']
    
    if not players:
        warnings.append("No player character declared in (:objects). You must declare one object of type 'player' (e.g. hero - player).")
        return warnings
        
    player = players[0]

    # Check JSON key mismatches
    if quest_data:
        json_keys = set()
        if "locations" in quest_data:
            json_keys.update(quest_data["locations"].keys())
        if "items" in quest_data:
            json_keys.update(quest_data["items"].keys())
        if "characters" in quest_data:
            json_keys.update(quest_data["characters"].keys())
            
        for obj in problem.objects:
            if obj not in json_keys and obj not in [player, 'hero', 'player']:
                matches = [k for k in json_keys if k in obj or obj in k]
                if matches:
                    warnings.append(f"Object '{obj}' in PDDL is not in the JSON keys. Did you mean '{matches[0]}'? You must rename it in PDDL to match JSON keys exactly.")
                else:
                    warnings.append(f"Object '{obj}' in PDDL is not in the JSON keys. Valid JSON keys are: {sorted(list(json_keys))}. You must rename it to match one of the JSON keys.")
    
    # Check undefined predicates in :init or :goal
    for fact in problem.init:
        pred = fact[0]
        if pred not in domain.predicates and pred not in ['=', 'not']:
            matches = [p for p in domain.predicates if p in pred or pred in p]
            if matches:
                warnings.append(f"Predicate '{pred}' in (:init) is not defined in domain.pddl. Did you mean '{matches[0]}'? Check domain.pddl predicates.")
            else:
                warnings.append(f"Predicate '{pred}' in (:init) is not defined in domain.pddl. Valid predicates are: {sorted(list(domain.predicates.keys()))}.")

    for fact in problem.goal_pos | problem.goal_neg:
        pred = fact[0]
        if pred not in domain.predicates and pred not in ['=', 'not']:
            matches = [p for p in domain.predicates if p in pred or pred in p]
            if matches:
                warnings.append(f"Predicate '{pred}' in (:goal) is not defined in domain.pddl. Did you mean '{matches[0]}'? Check domain.pddl predicates.")
            else:
                warnings.append(f"Predicate '{pred}' in (:goal) is not defined in domain.pddl. Valid predicates are: {sorted(list(domain.predicates.keys()))}.")

    # Check player starting location
    player_loc = None
    for fact in problem.init:
        if fact[0] == 'at' and len(fact) == 3 and fact[1] == player:
            player_loc = fact[2]
            break
    if not player_loc:
        warnings.append(f"Player '{player}' has no starting location in (:init). Add '(at {player} <location>)' to (:init).")
    elif player_loc not in locations:
        warnings.append(f"Player '{player}' starts at '{player_loc}', but '{player_loc}' is not declared as a location in (:objects).")

    # Check NPC locations and alive status
    for npc in npcs:
        npc_loc = None
        for fact in problem.init:
            if fact[0] == 'at' and len(fact) == 3 and fact[1] == npc:
                npc_loc = fact[2]
                break
        if not npc_loc:
            warnings.append(f"NPC '{npc}' has no starting location. Add '(at {npc} <location>)' to (:init).")
        elif npc_loc not in locations:
            warnings.append(f"NPC '{npc}' is at '{npc_loc}', but '{npc_loc}' is not declared as a location.")
            
        is_alive = False
        for fact in problem.init:
            if fact[0] == 'is-alive' and len(fact) == 2 and fact[1] == npc:
                is_alive = True
                break
        if not is_alive:
            warnings.append(f"NPC '{npc}' is not marked as alive. Add '(is-alive {npc})' to (:init).")

    # Check player alive status
    player_alive = False
    for fact in problem.init:
        if fact[0] == 'is-alive' and len(fact) == 2 and fact[1] == player:
            player_alive = True
            break
    if not player_alive:
        warnings.append(f"Player '{player}' is not marked as alive. Add '(is-alive {player})' to (:init).")

    # Check location connections
    for loc in locations:
        has_conn = False
        for fact in problem.init:
            if fact[0] == 'connected' and len(fact) == 3 and (fact[1] == loc or fact[2] == loc):
                has_conn = True
                break
        if not has_conn and len(locations) > 1:
            warnings.append(f"Location '{loc}' is disconnected. Define connections using '(connected {loc} <other>)' and '(connected <other> {loc})'.")

    # Check bidirectional connections
    connections = set()
    for fact in problem.init:
        if fact[0] == 'connected' and len(fact) == 3:
            connections.add((fact[1], fact[2]))
            
    for u, v in connections:
        if (v, u) not in connections:
            warnings.append(f"Connection between '{u}' and '{v}' is one-way. If it should be bidirectional, add '(connected {v} {u})' to (:init).")

    # Check locked locations and keys
    locked_locs = set()
    for fact in problem.init:
        if fact[0] == 'locked' and len(fact) == 2:
            locked_locs.add(fact[1])
            
    for loc in locked_locs:
        key_found = None
        for fact in problem.init:
            if fact[0] == 'key-for' and len(fact) == 3 and fact[2] == loc:
                key_found = fact[1]
                break
        if not key_found:
            warnings.append(f"Location '{loc}' is locked, but no key is assigned to it. Add '(key-for <key_item> {loc})' to (:init).")
        else:
            if key_found not in items:
                warnings.append(f"Key '{key_found}' for locked location '{loc}' is not declared as an item in (:objects).")
            # Check if key is obtainable
            key_obtainable = False
            for fact in problem.init:
                if (fact[0] == 'item-at' and len(fact) == 3 and fact[1] == key_found) or \
                   (fact[0] == 'has' and len(fact) == 3 and fact[2] == key_found):
                    key_obtainable = True
                    break
            if not key_obtainable:
                warnings.append(f"Key '{key_found}' for locked location '{loc}' is not placed at any location or held by any character in (:init). The player cannot obtain it.")

    # Check NPC satisfaction and wants-item
    for fact in problem.goal_pos:
        if fact[0] == 'npc-satisfied' and len(fact) == 2:
            target_npc = fact[1]
            if target_npc not in npcs:
                warnings.append(f"Goal requires satisfying '{target_npc}', but '{target_npc}' is not declared as an npc in (:objects).")
            else:
                has_wants = False
                for f in problem.init:
                    if f[0] == 'npc-wants-item' and len(f) == 3 and f[1] == target_npc:
                        has_wants = True
                        wanted_item = f[2]
                        if wanted_item not in items:
                            warnings.append(f"NPC '{target_npc}' wants '{wanted_item}', but '{wanted_item}' is not declared as an item in (:objects).")
                        # Check if wanted_item is obtainable
                        item_obtainable = False
                        for init_fact in problem.init:
                            if (init_fact[0] == 'item-at' and len(init_fact) == 3 and init_fact[1] == wanted_item) or \
                               (init_fact[0] == 'has' and len(init_fact) == 3 and init_fact[2] == wanted_item):
                                item_obtainable = True
                                break
                        if not item_obtainable:
                            warnings.append(f"Wanted item '{wanted_item}' for NPC '{target_npc}' is not placed anywhere or held by any character in (:init).")
                        break
                if not has_wants:
                    warnings.append(f"Goal requires satisfying NPC '{target_npc}', but there is no '(npc-wants-item {target_npc} <item>)' in (:init).")

    # Check item sources for goal items
    for fact in problem.goal_pos:
        if fact[0] == 'has' and len(fact) == 3 and fact[1] == player:
            goal_item = fact[2]
            if goal_item not in items:
                warnings.append(f"Goal requires player to have '{goal_item}', but '{goal_item}' is not declared as an item in (:objects).")
            else:
                item_obtainable = False
                for f in problem.init:
                    if (f[0] == 'item-at' and len(f) == 3 and f[1] == goal_item) or \
                       (f[0] == 'has' and len(f) == 3 and f[2] == goal_item):
                        item_obtainable = True
                        break
                if not item_obtainable:
                    warnings.append(f"Goal requires player to have '{goal_item}', but '{goal_item}' is not placed anywhere or held by any character in (:init) (so the player cannot obtain it).")

    return warnings

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
        
    parser = argparse.ArgumentParser(description="Generate a game story with a series of quests verified by STRIPS planning.")
    parser.add_argument("--prompt", type=str, help="Brief story concept prompt.")
    parser.add_argument("--model", type=str, default="qwen2.5:3b", help="Ollama model name (default: qwen2.5:3b).")
    parser.add_argument("--url", type=str, default="http://localhost:11434", help="Ollama URL (default: http://localhost:11434).")
    parser.add_argument("--output-dir", type=str, default="quests", help="Output directory (default: quests).")
    parser.add_argument("--max-repairs", type=int, default=10, help="Max repair attempts per quest (default: 10).")
    
    args = parser.parse_args()
    
    if not args.prompt:
        # Prompt interactively if not provided
        args.prompt = input("Enter a story concept/prompt: ").strip()
        if not args.prompt:
            print("Error: Prompt cannot be empty.")
            sys.exit(1)
            
    print(f"Connecting to Ollama at {args.url}...")
    models = check_ollama(args.url)
    if models is None:
        print("Error: Ollama is not running or unreachable at the given URL.")
        print("Please start Ollama (e.g. run 'ollama serve' in another terminal) and verify it is running.")
        sys.exit(1)
        
    print(f"Available models in Ollama: {', '.join(models)}")
    # If user specified model is not in list, find a fallback
    model_to_use = args.model
    if model_to_use not in models:
        # Check if versioned vs unversioned is present (e.g. qwen2.5:3b vs qwen2.5)
        matched = False
        for m in models:
            if m.startswith(model_to_use) or model_to_use.startswith(m):
                model_to_use = m
                matched = True
                break
        if not matched:
            # Fallback to the first model in the list
            if models:
                print(f"Warning: Model '{args.model}' not found in Ollama. Falling back to '{models[0]}'.")
                model_to_use = models[0]
            else:
                print("Error: No models found in Ollama. Please run 'ollama pull qwen2.5:3b' first.")
                sys.exit(1)
    else:
        print(f"Using model: {model_to_use}")
        
    # Read domain.pddl
    domain_path = "domain.pddl"
    if not os.path.exists(domain_path):
        print(f"Error: {domain_path} not found in current directory.")
        sys.exit(1)
        
    with open(domain_path, "r", encoding="utf-8") as f:
        domain_content = f.read()
        
    domain = Domain(domain_path)
    
    system_prompt = f"""
You are an expert game designer and PDDL planning specialist.
Your task is to generate a series of 3 coherent quests (a story arc) inspired by the user's short prompt.
The quests must use the PDDL domain defined in domain.pddl.
Here is the domain.pddl file:
{domain_content}

The output must be a single JSON object matching this schema:
{{
  "story_summary": "A brief overview of the 3-quest campaign.",
  "quests": [
    {{
      "quest_id": 1,
      "quest_title": "Title of Quest 1",
      "pddl_problem": "(define (problem quest_1) ... PDDL code ...)",
      "quest_data": {{
        "locations": {{
          "loc_id": {{
            "name": "Human-readable Name",
            "description": "Detailed description of the location.",
            "image_prompt": "Prompt for a diffusion model to generate location image."
          }}
        }},
        "items": {{
          "item_id": {{
            "name": "Human-readable Name",
            "description": "Detailed description of the item.",
            "image_prompt": "Prompt for a diffusion model to generate item image."
          }}
        }},
        "characters": {{
          "char_id": {{
            "name": "Human-readable Name",
            "description": "Detailed description of the character.",
            "image_prompt": "Prompt for a diffusion model to generate character image.",
            "dialogues": {{
              "before_talk": "First greeting dialogue.",
              "after_talk": "Dialogue if talked but goals not met.",
              "after_satisfied": "Dialogue after giving them their wanted item.",
              "hostile": "Dialogue if hostile (e.g. player stole from them)."
            }}
          }}
        }}
      }}
    }}
  ]
}}

CRITICAL PDDL RULES to prevent unsolvable quests:
1. Object types in the (:objects) block MUST use typing with the '-' character (e.g. hero - player, merchant - npc, key1 - item, village - location).
2. Every character (player or npc) MUST be declared as (is-alive name) in the (:init) block of the problem file.
3. The player character (must be of type 'player') must have an initial location, e.g. (at hero village).
4. The locations must be connected. If they are connected bidirectionally, you MUST define both: (connected loc1 loc2) AND (connected loc2 loc1).
5. If an NPC holds an item, you must set (has npc item). If the player is supposed to get it via 'receive-item', the item must be (grantable item) and the NPC must be alive (is-alive npc) and not hostile.
6. If the player needs to give an item to an NPC, the NPC must want it: (npc-wants-item npc item).
7. The goal of the quest should contain (npc-satisfied npc) if the player is supposed to complete a trade with that NPC.
8. If a location is locked, you must set (locked loc), specify the key (key-for key_item loc), and put the key somewhere the player can find/earn.
9. Object IDs (locations, items, characters) used in PDDL must match the keys in the JSON quest_data exactly, and must be simple lowercase alphanumeric strings (e.g. old-merchant, brass-key, hero, castle).
10. Do not reference objects in PDDL that are not defined in the (:objects) block.

FEW-SHOT EXAMPLE OF A VALID QUEST DEFINITION:
{{
  "quest_id": 1,
  "quest_title": "Obtain the Key",
  "pddl_problem": "(define (problem quest_1)\\n  (:domain magic-world)\\n  (:objects\\n    hero - player\\n    merchant - npc\\n    potion brass-key - item\\n    village tower-entrance - location\\n  )\\n  (:init\\n    (at hero village)\\n    (at merchant village)\\n    (is-alive hero)\\n    (is-alive merchant)\\n    (item-at potion village)\\n    (connected village tower-entrance)\\n    (connected tower-entrance village)\\n    (locked tower-entrance)\\n    (key-for brass-key tower-entrance)\\n    (has merchant brass-key)\\n    (npc-wants-item merchant potion)\\n    (grantable brass-key)\\n  )\\n  (:goal (and\\n    (npc-satisfied merchant)\\n    (has hero brass-key)\\n  ))\\n)",
  "quest_data": {{
    "locations": {{
      "village": {{
        "name": "Village Square",
        "description": "A bustling market square filled with people.",
        "image_prompt": "fantasy village square, watercolor style"
      }},
      "tower-entrance": {{
        "name": "Tower Gates",
        "description": "The imposing heavy gates of the ancient tower.",
        "image_prompt": "dark stone tower gates, fantasy art"
      }}
    }},
    "items": {{
      "potion": {{
        "name": "Magic Potion",
        "description": "A bottle filled with glowing blue liquid.",
        "image_prompt": "glowing blue potion bottle"
      }},
      "brass-key": {{
        "name": "Heavy Brass Key",
        "description": "A heavy brass key designed to open the tower gate.",
        "image_prompt": "old brass key, fantasy style"
      }}
    }},
    "characters": {{
      "hero": {{
        "name": "Alden",
        "description": "A brave apprentice searcher of lost relics.",
        "image_prompt": "young adventurer, fantasy art"
      }},
      "merchant": {{
        "name": "Garrick the Merchant",
        "description": "A merchant who holds the tower key.",
        "image_prompt": "wealthy medieval merchant",
        "dialogues": {{
          "before_talk": "Garrick: Bring me a potion and I will grant you the key.",
          "after_talk": "Garrick: Still looking for the potion? Go to the tavern.",
          "after_satisfied": "Garrick: Wonderful! Here is the brass key.",
          "hostile": "Garrick: Thief! Guards, help!"
        }}
      }}
    }}
  }}
}}
"""

    print("Generating story quests... (this might take a minute)")
    user_prompt = f"Please generate a 3-quest campaign based on this prompt: '{args.prompt}'."
    
    response = call_ollama(user_prompt, model_to_use, args.url, system_prompt)
    if not response:
        print("Error: Empty response or failed connection to Ollama.")
        sys.exit(1)
        
    try:
        story_data = json.loads(response)
    except Exception as e:
        print(f"Error parsing Ollama response as JSON: {e}")
        print("Raw response was:")
        print(response)
        sys.exit(1)
        
    print("\nStory campaign generated successfully!")
    print(f"Story Summary: {story_data.get('story_summary', '')}\n")
    
    campaign_slug = get_campaign_slug(args.prompt)
    campaign_dir = os.path.join(args.output_dir, campaign_slug)
    raw_dir = os.path.join(campaign_dir, "raw")
    
    os.makedirs(campaign_dir, exist_ok=True)
    os.makedirs(raw_dir, exist_ok=True)
    
    # Save the original prompt
    with open(os.path.join(campaign_dir, "original_prompt.txt"), "w", encoding="utf-8") as f:
        f.write(args.prompt)
        
    quests = story_data.get("quests", [])
    if not quests:
        print("Error: No quests found in response.")
        sys.exit(1)
        
    # Save raw backup first
    for q in quests:
        q_id = q.get("quest_id", 1)
        raw_pddl_file = os.path.join(raw_dir, f"quest_{q_id}.pddl")
        raw_json_file = os.path.join(raw_dir, f"quest_{q_id}.json")
        with open(raw_pddl_file, "w", encoding="utf-8") as f:
            f.write(q.get("pddl_problem", ""))
        with open(raw_json_file, "w", encoding="utf-8") as f:
            json.dump(q.get("quest_data", {}), f, indent=2, ensure_ascii=False)
        
    for quest in quests:
        quest_id = quest.get("quest_id", 1)
        quest_title = quest.get("quest_title", f"Quest {quest_id}")
        pddl_problem = quest.get("pddl_problem", "")
        quest_data = quest.get("quest_data", {})
        
        print(f"--- Verifying Quest {quest_id}: {quest_title} ---")
        
        # Repair loop
        solved = False
        plan = None
        attempt = 0
        
        while not solved and attempt <= args.max_repairs:
            attempt += 1
            pddl_problem = auto_repair_pddl(pddl_problem, quest_data, domain)
            # Try to parse and solve
            try:
                prob = Problem(pddl_problem, is_content=True)
                plan = solve_pddl(domain, prob)
                if plan is not None:
                    if len(plan) > 0:
                        solved = True
                        break
                    else:
                        error_msg = "The goal is already satisfied in the initial state! The quest must require at least one action (e.g. move, talk, unlock) to be solved."
                else:
                    warnings = diagnose_pddl_problem(prob, domain)
                    if warnings:
                        error_msg = "No path to the goal exists. The following specific logic issues were found:\n" + "\n".join(f"- {w}" for w in warnings)
                    else:
                        error_msg = "No path to the goal exists. Check if location connections are defined bidirectionally, if NPCs have items, and if NPCs/player are marked as (is-alive) in the :init state."
            except Exception as e:
                error_msg = f"PDDL Parser error: {e}"
                
            if solved:
                break
                
            if attempt > args.max_repairs:
                print(f"Failed to repair Quest {quest_id} after {args.max_repairs} attempts.")
                break
                
            print(f"Attempt {attempt}: Quest {quest_id} is unsolvable/invalid. Prompting LLM for repair...")
            print(f"Planner error:\n{error_msg}")
            
            repair_prompt = f"""
The quest you generated is unsolvable.
The STRIPS planning solver failed to find a plan for Quest {quest_id}.
Reason / Planner output: {error_msg}

The quests must use the PDDL domain defined in domain.pddl.
Here is the domain.pddl file for reference:
{domain_content}

Here is the PDDL problem you generated:
```lisp
{pddl_problem}
```

Here is the JSON data you generated:
```json
{json.dumps(quest_data, indent=2)}
```

Please fix the PDDL problem and JSON data for this quest.
Make sure that:
- Every character is alive: (is-alive char_name) in :init.
- The player starts at a location.
- All connections (connected loc1 loc2) are set correctly and bidirectionally if needed.
- If the goal requires a character to be satisfied or have an item, the path of actions is logically solvable.
- Return the output as a valid JSON object matching the schema for a single quest:
{{
  "quest_id": {quest_id},
  "quest_title": "{quest_title}",
  "pddl_problem": "(define (problem quest_{quest_id}) ... PDDL code ...)",
  "quest_data": {{ ... }}
}}
"""
            # Ask the LLM to fix it
            repair_response = call_ollama(repair_prompt, model_to_use, args.url, "You are a helpful assistant that corrects PDDL and JSON files.")
            if not repair_response:
                print("Error: Failed to get repair response from Ollama.")
                break
                
            try:
                repaired_quest = json.loads(repair_response)
                pddl_problem = repaired_quest.get("pddl_problem", pddl_problem)
                quest_data = repaired_quest.get("quest_data", quest_data)
            except Exception as e:
                print(f"Error parsing repair response as JSON: {e}")
                # Try to extract JSON using regex if Ollama didn't return perfect JSON
                # but format: json is set, so it should be valid JSON
                pass
                
        if solved and plan:
            print(f"Success! Quest {quest_id} is solvable.")
            print("Plan:")
            for step in plan:
                print(f"  {step}")
        else:
            print(f"Warning: Quest {quest_id} is being saved but is UNSOLVABLE by the STRIPS planner.")
            
        # Save files
        pddl_file = os.path.join(campaign_dir, f"quest_{quest_id}.pddl")
        json_file = os.path.join(campaign_dir, f"quest_{quest_id}.json")
        
        with open(pddl_file, "w", encoding="utf-8") as f:
            f.write(pddl_problem)
            
        # Add solver status and plan to the JSON for reference
        quest_data["solvable"] = solved
        if solved and plan:
            quest_data["expected_plan"] = [step.name for step in plan]
        else:
            quest_data["expected_plan"] = []
            
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(quest_data, f, indent=2, ensure_ascii=False)
            
        print(f"Saved: {pddl_file} and {json_file}\n")
        
    print("Generation complete! Quests saved in directory:", campaign_dir)

if __name__ == "__main__":
    main()
