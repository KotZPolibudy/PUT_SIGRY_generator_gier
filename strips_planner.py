import re
import itertools
from collections import deque

def remove_comments(text):
    lines = []
    for line in text.splitlines():
        if ';' in line:
            line = line.split(';', 1)[0]
        lines.append(line)
    return '\n'.join(lines)

def tokenize(text):
    return re.findall(r'\(|\)|[^\s()]+', text)

def parse_tokens(tokens):
    if not tokens:
        raise ValueError("Unexpected EOF")
    token = tokens.pop(0)
    if token == '(':
        lst = []
        while tokens and tokens[0] != ')':
            lst.append(parse_tokens(tokens))
        if tokens:
            tokens.pop(0) # pop ')'
        return lst
    elif token == ')':
        raise ValueError("Unexpected )")
    else:
        return token

def parse_pddl_text(text):
    clean_text = remove_comments(text)
    tokens = tokenize(clean_text)
    if not tokens:
        return []
    try:
        return parse_tokens(tokens)
    except Exception as e:
        print(f"Error parsing PDDL: {e}")
        return []

def parse_types(types_def):
    hierarchy = {}
    current_children = []
    i = 0
    elements = types_def[1:]
    while i < len(elements):
        item = elements[i]
        if item == '-':
            parent = elements[i+1]
            for child in current_children:
                hierarchy[child] = parent
            current_children = []
            i += 2
        else:
            hierarchy[item] = 'object'
            current_children.append(item)
            i += 1
    # Handle any remaining children that didn't have explicit parent
    for child in current_children:
        hierarchy[child] = 'object'
    return hierarchy

def parse_typed_list(elements):
    parsed = []
    current_vars = []
    i = 0
    while i < len(elements):
        item = elements[i]
        if item == '-':
            var_type = elements[i+1]
            for var in current_vars:
                parsed.append((var, var_type))
            current_vars = []
            i += 2
        else:
            current_vars.append(item)
            i += 1
    for var in current_vars:
        parsed.append((var, 'object'))
    return parsed

def parse_condition(expr):
    def deep_tuple(val):
        if isinstance(val, list):
            return tuple(deep_tuple(x) for x in val)
        return val
        
    pos = set()
    neg = set()
    if not expr:
        return pos, neg
    
    if isinstance(expr, list):
        if expr[0] == 'and':
            for sub in expr[1:]:
                p, n = parse_condition(sub)
                pos.update(p)
                neg.update(n)
        elif expr[0] == 'not':
            sub = expr[1]
            if isinstance(sub, list):
                neg.add(deep_tuple(sub))
            else:
                raise ValueError(f"Invalid negative literal: {expr}")
        else:
            pos.add(deep_tuple(expr))
    else:
        pos.add((expr,))
    return pos, neg

def is_subtype(child, parent, hierarchy):
    if child == parent:
        return True
    if parent == 'object':
        return True
    current = child
    visited = set()
    while current in hierarchy:
        if current in visited:
            break
        visited.add(current)
        current = hierarchy[current]
        if current == parent:
            return True
    return False

class Action:
    def __init__(self, expr):
        self.name = expr[1]
        self.parameters = []
        self.pre_pos = set()
        self.pre_neg = set()
        self.eff_pos = set()
        self.eff_neg = set()
        
        i = 2
        while i < len(expr):
            key = expr[i]
            if key == ':parameters':
                self.parameters = parse_typed_list(expr[i+1])
                i += 2
            elif key == ':precondition':
                self.pre_pos, self.pre_neg = parse_condition(expr[i+1])
                i += 2
            elif key == ':effect':
                self.eff_pos, self.eff_neg = parse_condition(expr[i+1])
                i += 2
            else:
                i += 1

class Domain:
    def __init__(self, filename_or_content, is_content=False):
        if is_content:
            content = filename_or_content
        else:
            with open(filename_or_content, 'r', encoding='utf-8') as f:
                content = f.read()
        self.tree = parse_pddl_text(content)
        self.name = ""
        self.types = {}
        self.predicates = {}
        self.actions = []
        self._parse()

    def _parse(self):
        if not self.tree or self.tree[0] != 'define':
            raise ValueError("Invalid PDDL domain structure")
            
        for item in self.tree[1:]:
            if not isinstance(item, list):
                continue
            head = item[0]
            if head == 'domain':
                self.name = item[1]
            elif head == ':types':
                self.types = parse_types(item)
            elif head == ':predicates':
                for pred in item[1:]:
                    if isinstance(pred, list):
                        self.predicates[pred[0]] = pred[1:]
            elif head == ':action':
                self.actions.append(Action(item))

class Problem:
    def __init__(self, filename_or_content, is_content=False):
        if is_content:
            content = filename_or_content
        else:
            with open(filename_or_content, 'r', encoding='utf-8') as f:
                content = f.read()
        self.tree = parse_pddl_text(content)
        self.name = ""
        self.domain_name = ""
        self.objects = {}
        self.init = set()
        self.goal_pos = set()
        self.goal_neg = set()
        self._parse()
        
    def _parse(self):
        if not self.tree or self.tree[0] != 'define':
            raise ValueError("Invalid PDDL problem structure")
            
        for item in self.tree[1:]:
            if not isinstance(item, list):
                continue
            head = item[0]
            if head == 'problem':
                self.name = item[1]
            elif head == ':domain':
                self.domain_name = item[1]
            elif head == ':objects':
                parsed_objs = parse_typed_list(item[1:])
                self.objects = {obj: otype for obj, otype in parsed_objs}
            elif head == ':init':
                def make_hashable(val):
                    if isinstance(val, list):
                        return tuple(make_hashable(x) for x in val)
                    return val
                for fact in item[1:]:
                    if isinstance(fact, list):
                        if fact[0] == 'not':
                            continue
                        self.init.add(make_hashable(fact))
            elif head == ':goal':
                self.goal_pos, self.goal_neg = parse_condition(item[1])
                
        # Validate that all objects used in init or goal are declared
        referenced = set()
        for fact in self.init:
            for term in fact[1:]:
                referenced.add(term)
        for fact in self.goal_pos:
            for term in fact[1:]:
                referenced.add(term)
        for fact in self.goal_neg:
            for term in fact[1:]:
                referenced.add(term)
                
        undeclared = referenced - set(self.objects.keys())
        if undeclared:
            raise ValueError(f"Objects {list(undeclared)} are used in :init or :goal, but are not declared in the (:objects) block. You must declare all locations, items, and characters with their types (e.g. obj1 - type) in (:objects).")

class GroundedAction:
    def __init__(self, name, original_name, args, pre_pos, pre_neg, eff_pos, eff_neg):
        self.name = name
        self.original_name = original_name
        self.args = args
        self.pre_pos = frozenset(pre_pos)
        self.pre_neg = frozenset(pre_neg)
        self.eff_pos = frozenset(eff_pos)
        self.eff_neg = frozenset(eff_neg)

    def __repr__(self):
        return self.name

def ground_actions(domain, problem):
    all_types = set(domain.types.keys()) | set(domain.types.values()) | {'object'}
    type_objects = {}
    
    for t in all_types:
        type_objects[t] = []
        for obj, obj_type in problem.objects.items():
            if is_subtype(obj_type, t, domain.types):
                type_objects[t].append(obj)
                
    grounded = []
    for action in domain.actions:
        param_names = [p[0] for p in action.parameters]
        param_types = [p[1] for p in action.parameters]
        
        param_obj_lists = []
        for pt in param_types:
            param_obj_lists.append(type_objects.get(pt, []))
            
        for combination in itertools.product(*param_obj_lists):
            mapping = dict(zip(param_names, combination))
            
            g_pre_pos = set()
            for literal in action.pre_pos:
                g_pre_pos.add(tuple(mapping.get(sym, sym) for sym in literal))
                
            g_pre_neg = set()
            for literal in action.pre_neg:
                g_pre_neg.add(tuple(mapping.get(sym, sym) for sym in literal))
                
            g_eff_pos = set()
            for literal in action.eff_pos:
                g_eff_pos.add(tuple(mapping.get(sym, sym) for sym in literal))
                
            g_eff_neg = set()
            for literal in action.eff_neg:
                g_eff_neg.add(tuple(mapping.get(sym, sym) for sym in literal))
                
            name = f"({action.name} " + " ".join(combination) + ")"
            grounded.append(GroundedAction(name, action.name, list(combination), g_pre_pos, g_pre_neg, g_eff_pos, g_eff_neg))
            
    return grounded

def solve_pddl(domain, problem, max_states=15000):
    grounded = ground_actions(domain, problem)
    init_state = frozenset(problem.init)
    
    queue = deque([(init_state, [])])
    visited = {init_state}
    
    while queue:
        state, path = queue.popleft()
        
        if problem.goal_pos.issubset(state) and problem.goal_neg.isdisjoint(state):
            return path
            
        if len(visited) > max_states:
            return None
            
        for action in grounded:
            if action.pre_pos.issubset(state) and action.pre_neg.isdisjoint(state):
                next_state = frozenset((state - action.eff_neg) | action.eff_pos)
                if next_state not in visited:
                    visited.add(next_state)
                    queue.append((next_state, path + [action]))
                    
    return None
