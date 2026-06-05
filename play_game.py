import os
import sys
import json
from strips_planner import Domain, Problem, ground_actions, solve_pddl

# ANSI escape codes for coloring
COLOR_HEADER = "\033[95m"
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"

def supports_color():
    # Check if stdout is a tty and if OS is not Windows without ANSI support
    plat = sys.platform
    supported_platform = plat != 'win32' or 'ANSICON' in os.environ
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    # Check Windows 10 color support
    if plat == 'win32' and not supported_platform:
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # Enable VT100 emulation on Windows command prompt
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            supported_platform = True
        except Exception:
            pass
    return supported_platform and is_a_tty

# Toggle color based on support
USE_COLOR = supports_color()

def color_text(text, color):
    if USE_COLOR:
        return f"{color}{text}{COLOR_RESET}"
    return text

def get_obj_name(obj_id, quest_data):
    for category in ["locations", "items", "characters"]:
        if category in quest_data and obj_id in quest_data[category]:
            return quest_data[category][obj_id].get("name", obj_id)
    return obj_id

def get_obj_desc(obj_id, quest_data):
    for category in ["locations", "items", "characters"]:
        if category in quest_data and obj_id in quest_data[category]:
            return quest_data[category][obj_id].get("description", "")
    return ""

def get_character_dialogue(char_id, state, quest_data):
    char_info = quest_data.get("characters", {}).get(char_id, {})
    dialogues = char_info.get("dialogues", {})
    
    # Check dialogue state based on predicates in the state
    if ("is-hostile", char_id) in state:
        return dialogues.get("hostile", "Get away from me!")
    elif ("npc-satisfied", char_id) in state:
        return dialogues.get("after_satisfied", "Thank you for your help.")
    elif ("has-talked", "hero", char_id) in state:
        return dialogues.get("after_talk", "Yes? Do you need something else?")
    else:
        return dialogues.get("before_talk", "Hello.")

def translate_action(action, quest_data):
    name = action.original_name
    args = action.args
    arg_names = [get_obj_name(arg, quest_data) for arg in args]
    
    if name == "move":
        return f"Go to {arg_names[2]}"
    elif name == "unlock":
        return f"Unlock {arg_names[2]} using {arg_names[3]}"
    elif name == "pick-up":
        return f"Pick up {arg_names[1]}"
    elif name == "loot":
        return f"Loot {arg_names[2]} from {arg_names[1]}'s body"
    elif name == "talk":
        return f"Talk to {arg_names[1]}"
    elif name == "give-item":
        return f"Give {arg_names[2]} to {arg_names[1]}"
    elif name == "receive-item":
        return f"Ask {arg_names[1]} for {arg_names[2]}"
    elif name == "steal":
        return f"Steal {arg_names[2]} from {arg_names[1]}"
    elif name == "kill":
        return f"Attack {arg_names[1]} using {arg_names[3]}"
    else:
        return f"Execute {name} on " + ", ".join(arg_names)

def find_player_location(state):
    for fact in state:
        if len(fact) == 3 and fact[0] == "at" and fact[1] == "hero":
            return fact[2]
    return None

def is_still_solvable(domain, problem, current_state):
    # Create a temporary problem representation with current_state as init
    # We copy the problem and set its init state to current_state
    import copy
    temp_prob = copy.copy(problem)
    temp_prob.init = current_state
    plan = solve_pddl(domain, temp_prob, max_states=1000)
    return plan is not None

def play_quest(domain_path, pddl_path, json_path):
    # Load Domain
    domain = Domain(domain_path)
    
    # Load Problem & JSON
    problem = Problem(pddl_path)
    with open(json_path, "r", encoding="utf-8") as f:
        quest_data = json.load(f)
        
    state = set(problem.init)
    history = []
    
    print("\n" + "="*50)
    print(color_text(f"QUEST START: {quest_data.get('name', problem.name).upper()}", COLOR_HEADER + COLOR_BOLD))
    print(f"Goal: {color_text('And', COLOR_BOLD)} the following predicates:")
    for fact in problem.goal_pos:
        fact_str = f"({fact[0]} " + " ".join(fact[1:]) + ")"
        print(f"  - {color_text(fact_str, COLOR_GREEN)}")
    for fact in problem.goal_neg:
        fact_str = f"(not ({fact[0]} " + " ".join(fact[1:]) + "))"
        print(f"  - {color_text(fact_str, COLOR_RED)}")
    print("="*50 + "\n")
    
    while True:
        # Check Goal
        if problem.goal_pos.issubset(state) and problem.goal_neg.isdisjoint(state):
            print("\n" + "*"*40)
            print(color_text("QUEST COMPLETED!", COLOR_GREEN + COLOR_BOLD))
            print("*"*40 + "\n")
            return True
            
        # Get current location
        loc_id = find_player_location(state)
        if not loc_id:
            print(color_text("Error: Player location could not be determined from state!", COLOR_RED))
            return False
            
        loc_name = get_obj_name(loc_id, quest_data)
        loc_desc = get_obj_desc(loc_id, quest_data)
        
        # Display state
        print(color_text(f"\nLocation: {loc_name}", COLOR_CYAN + COLOR_BOLD))
        if loc_desc:
            print(f"{loc_desc}")
            
        # Display NPCs here
        npcs_here = []
        for fact in state:
            if len(fact) == 3 and fact[0] == "at" and fact[2] == loc_id and fact[1] != "hero":
                npcs_here.append(fact[1])
                
        if npcs_here:
            print(color_text("Characters present:", COLOR_YELLOW))
            for npc in npcs_here:
                npc_name = get_obj_name(npc, quest_data)
                npc_desc = get_obj_desc(npc, quest_data)
                alive = ("is-alive", npc) in state
                hostile = ("is-hostile", npc) in state
                status_str = "Alive" if alive else "Dead"
                if hostile:
                    status_str += ", Hostile"
                else:
                    status_str += ", Friendly"
                desc_str = f" - {npc_desc}" if npc_desc else ""
                print(f"  * {npc_name} ({color_text(status_str, COLOR_RED if hostile or not alive else COLOR_GREEN)}){desc_str}")
                
        # Display Items here
        items_here = []
        for fact in state:
            if len(fact) == 3 and fact[0] == "item-at" and fact[2] == loc_id:
                items_here.append(fact[1])
                
        if items_here:
            print(color_text("Items on the ground:", COLOR_GREEN))
            for item in items_here:
                item_name = get_obj_name(item, quest_data)
                item_desc = get_obj_desc(item, quest_data)
                desc_str = f" - {item_desc}" if item_desc else ""
                print(f"  * {item_name}{desc_str}")
                
        # Display Inventory
        inventory = []
        for fact in state:
            if len(fact) == 3 and fact[0] == "has" and fact[1] == "hero":
                inventory.append(fact[2])
                
        inventory_names = [get_obj_name(item, quest_data) for item in inventory]
        print(f"Inventory: {color_text(', '.join(inventory_names) if inventory_names else 'Empty', COLOR_BLUE)}")
        
        # Check Solvability
        if not is_still_solvable(domain, problem, state):
            print(color_text("\n[WARNING] You have reached a dead end! This quest is no longer solvable.", COLOR_RED + COLOR_BOLD))
            print(color_text("You can type 'u' to undo, 'r' to restart, or 'q' to quit.", COLOR_YELLOW))
            
        # Ground and find applicable actions
        grounded = ground_actions(domain, problem)
        applicable_actions = []
        for action in grounded:
            if action.pre_pos.issubset(state) and action.pre_neg.isdisjoint(state):
                applicable_actions.append(action)
                
        # Present menu
        print(color_text("\nAvailable Actions:", COLOR_BOLD))
        for idx, action in enumerate(applicable_actions, 1):
            action_desc = translate_action(action, quest_data)
            print(f"  {idx}. {action_desc}")
            
        print(color_text("\nSystem Commands:", COLOR_BOLD))
        print("  u. Undo last action")
        print("  r. Restart quest")
        print("  q. Quit game")
        
        choice = input("\nChoose an action: ").strip().lower()
        
        if choice == 'q':
            print("Quitting game. Goodbye!")
            sys.exit(0)
        elif choice == 'r':
            history.clear()
            state = set(problem.init)
            print(color_text("\nQuest restarted!", COLOR_YELLOW))
            continue
        elif choice == 'u':
            if history:
                state = history.pop()
                print(color_text("\nUndid last action.", COLOR_YELLOW))
            else:
                print(color_text("\nNothing to undo.", COLOR_RED))
            continue
            
        try:
            action_idx = int(choice) - 1
            if 0 <= action_idx < len(applicable_actions):
                selected_action = applicable_actions[action_idx]
                
                # Push state to history
                history.append(set(state))
                
                # Apply action effects
                old_state = set(state)
                state = (state - selected_action.eff_neg) | selected_action.eff_pos
                
                # Execution description and dialogues
                print(color_text(f"\n> You performed: {translate_action(selected_action, quest_data)}", COLOR_BOLD + COLOR_GREEN))
                
                act_name = selected_action.original_name
                args = selected_action.args
                
                if act_name == "talk":
                    char_id = args[1]
                    char_name = get_obj_name(char_id, quest_data)
                    # Show dialogue. Note: we evaluate using the OLD state before 'has-talked' is set, 
                    # but we can pass the old state because that shows before_talk properly
                    dialogue = get_character_dialogue(char_id, old_state, quest_data)
                    print(f'\n{color_text(char_name, COLOR_YELLOW)}: "{color_text(dialogue, COLOR_BOLD)}"')
                elif act_name == "give-item":
                    char_id = args[1]
                    char_name = get_obj_name(char_id, quest_data)
                    # We evaluate dialogues using the new state since they are now satisfied
                    dialogue = get_character_dialogue(char_id, state, quest_data)
                    print(f'\n{color_text(char_name, COLOR_YELLOW)}: "{color_text(dialogue, COLOR_BOLD)}"')
                elif act_name == "receive-item":
                    char_id = args[1]
                    item_name = get_obj_name(args[2], quest_data)
                    char_name = get_obj_name(char_id, quest_data)
                    print(f"You received the {color_text(item_name, COLOR_GREEN)} from {color_text(char_name, COLOR_YELLOW)}.")
                elif act_name == "steal":
                    char_id = args[1]
                    item_name = get_obj_name(args[2], quest_data)
                    char_name = get_obj_name(char_id, quest_data)
                    print(f"You stole the {color_text(item_name, COLOR_RED)} from {color_text(char_name, COLOR_YELLOW)}!")
                    # NPC becomes hostile and shouts
                    dialogue = get_character_dialogue(char_id, state, quest_data)
                    print(f'\n{color_text(char_name, COLOR_YELLOW)}: "{color_text(dialogue, COLOR_RED + COLOR_BOLD)}"')
                elif act_name == "kill":
                    char_id = args[1]
                    char_name = get_obj_name(char_id, quest_data)
                    print(f"You attacked {color_text(char_name, COLOR_RED)} with {get_obj_name(args[3], quest_data)}! {color_text(char_name, COLOR_RED)} falls to the ground, dead.")
                elif act_name == "loot":
                    char_id = args[1]
                    item_name = get_obj_name(args[2], quest_data)
                    print(f"You looted {color_text(item_name, COLOR_GREEN)} from the corpse of {color_text(get_obj_name(char_id, quest_data), COLOR_RED)}.")
                elif act_name == "pick-up":
                    print(f"You picked up {color_text(get_obj_name(args[1], quest_data), COLOR_GREEN)}.")
                elif act_name == "unlock":
                    print(f"You unlocked the way to {color_text(get_obj_name(args[2], quest_data), COLOR_CYAN)} using {color_text(get_obj_name(args[3], quest_data), COLOR_GREEN)}.")
                elif act_name == "move":
                    print(f"You travelled to {color_text(get_obj_name(args[2], quest_data), COLOR_CYAN)}.")
                    
            else:
                print(color_text("Invalid action number.", COLOR_RED))
        except ValueError:
            print(color_text("Invalid input. Please enter a number or command letter.", COLOR_RED))

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
        
    import glob
    
    quests_dir = "quests"
    if not os.path.exists(quests_dir):
        print(f"Error: Directory '{quests_dir}' not found. Please run generate_story.py first.")
        sys.exit(1)
        
    # Find all subdirectories
    subdirs = []
    if os.path.exists(quests_dir):
        subdirs = [d for d in os.listdir(quests_dir) if os.path.isdir(os.path.join(quests_dir, d)) and d != "raw"]
    
    campaigns = []
    # Check each subdirectory for quest files
    for subdir in subdirs:
        campaign_path = os.path.join(quests_dir, subdir)
        pddl_files = sorted(glob.glob(os.path.join(campaign_path, "quest_*.pddl")))
        json_files = sorted(glob.glob(os.path.join(campaign_path, "quest_*.json")))
        
        if pddl_files and json_files:
            prompt = subdir
            prompt_file = os.path.join(campaign_path, "original_prompt.txt")
            if os.path.exists(prompt_file):
                with open(prompt_file, "r", encoding="utf-8") as f:
                    prompt = f.read().strip()
            campaigns.append({
                "dir_name": subdir,
                "path": campaign_path,
                "prompt": prompt,
                "pddl_files": pddl_files,
                "json_files": json_files
            })
            
    # Check if there are legacy quests directly in quests_dir
    legacy_pddl = sorted(glob.glob(os.path.join(quests_dir, "quest_*.pddl")))
    legacy_json = sorted(glob.glob(os.path.join(quests_dir, "quest_*.json")))
    if legacy_pddl and legacy_json:
        prompt = "Legacy Campaign"
        prompt_file = os.path.join(quests_dir, "original_prompt.txt")
        if os.path.exists(prompt_file):
            with open(prompt_file, "r", encoding="utf-8") as f:
                prompt = f.read().strip()
        campaigns.append({
            "dir_name": "legacy",
            "path": quests_dir,
            "prompt": prompt,
            "pddl_files": legacy_pddl,
            "json_files": legacy_json
        })
        
    if not campaigns:
        print(f"Error: No campaigns or quest files found in '{quests_dir}'.")
        print("Please generate a campaign using generate_story.py first.")
        sys.exit(1)
        
    selected_campaign = None
    if len(campaigns) == 1:
        selected_campaign = campaigns[0]
        print(color_text(f"Only one campaign found, loading automatically: {selected_campaign['prompt']}", COLOR_YELLOW))
    else:
        print(color_text("="*60, COLOR_HEADER + COLOR_BOLD))
        print(color_text("                 SELECT A CAMPAIGN TO PLAY                     ", COLOR_HEADER + COLOR_BOLD))
        print(color_text("="*60, COLOR_HEADER + COLOR_BOLD))
        for idx, camp in enumerate(campaigns, 1):
            print(f"  {idx}. {color_text(camp['prompt'], COLOR_GREEN + COLOR_BOLD)}")
            print(f"     Folder: {camp['dir_name']} ({len(camp['pddl_files'])} quests)")
        print()
        
        while True:
            choice = input(f"Choose a campaign (1-{len(campaigns)}): ").strip()
            try:
                c_idx = int(choice) - 1
                if 0 <= c_idx < len(campaigns):
                    selected_campaign = campaigns[c_idx]
                    break
                else:
                    print(color_text("Invalid selection. Try again.", COLOR_RED))
            except ValueError:
                print(color_text("Please enter a valid number.", COLOR_RED))
                
    pddl_files = selected_campaign["pddl_files"]
    json_files = selected_campaign["json_files"]
    
    print(color_text("\n" + "="*60, COLOR_HEADER + COLOR_BOLD))
    print(color_text("                 GAME GENERATOR - QUEST PLAYER                 ", COLOR_HEADER + COLOR_BOLD))
    print(color_text("="*60, COLOR_HEADER + COLOR_BOLD))
    print(f"\nStory Prompt: {color_text(selected_campaign['prompt'], COLOR_BOLD)}")
    print(f"Found {len(pddl_files)} quests in campaign.\n")
    
    for i in range(len(pddl_files)):
        pddl_path = pddl_files[i]
        json_path = json_files[i]
        
        success = play_quest("domain.pddl", pddl_path, json_path)
        if not success:
            print(color_text("Failed to complete quest. Campaign halted.", COLOR_RED))
            sys.exit(1)
            
    print(color_text("\n" + "="*60, COLOR_GREEN + COLOR_BOLD))
    print(color_text("          VICTORY! YOU COMPLETED THE ENTIRE CAMPAIGN!          ", COLOR_GREEN + COLOR_BOLD))
    print(color_text("="*60 + "\n", COLOR_GREEN + COLOR_BOLD))

if __name__ == "__main__":
    main()
