import os
import unittest
from strips_planner import Domain, Problem, solve_pddl

class TestSTRIPSPlanner(unittest.TestCase):
    def test_basic_planning(self):
        # We assume domain.pddl is in the same directory
        domain_path = "domain.pddl"
        self.assertTrue(os.path.exists(domain_path), "domain.pddl not found!")
        
        domain = Domain(domain_path)
        
        # Define a simple problem in PDDL format
        problem_pddl = """
        (define (problem quest1)
            (:domain magic-world)
            (:objects
                hero - player
                old-merchant - npc
                potion key1 - item
                village library - location
            )
            (:init
                (at hero village)
                (at old-merchant village)
                (is-alive hero)
                (is-alive old-merchant)
                (item-at potion village)
                (connected village library)
                (locked library)
                (key-for key1 library)
                (has old-merchant key1)
                (npc-wants-item old-merchant potion)
                (grantable key1)
            )
            (:goal (and
                (npc-satisfied old-merchant)
                (at hero library)
            ))
        )
        """
        
        problem = Problem(problem_pddl, is_content=True)
        
        # Solve
        plan = solve_pddl(domain, problem)
        self.assertIsNotNone(plan, "Planner failed to find a plan!")
        
        # Verify plan sequence
        plan_names = [a.name for a in plan]
        print("Found plan:")
        for step in plan_names:
            print(f"  {step}")
            
        self.assertEqual(len(plan), 6)
        self.assertEqual(plan[0].original_name, "pick-up")
        self.assertEqual(plan[1].original_name, "talk")
        self.assertEqual(plan[2].original_name, "give-item")
        self.assertEqual(plan[3].original_name, "receive-item")
        self.assertEqual(plan[4].original_name, "unlock")
        self.assertEqual(plan[5].original_name, "move")

if __name__ == "__main__":
    unittest.main()
