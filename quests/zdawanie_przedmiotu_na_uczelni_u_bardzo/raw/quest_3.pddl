(define (problem quest_3)
  (:domain magic-world)
  (:objects
    alyssa - player
    professor - npc
    final_exam_paper - item
    classroom - location
  )
  (:init
    (at alyssa university_building)
    (is-alive alyssa)
    (is-alive professor)
    (locked classroom)
    (key-for key3 classroom)
    (has professor key3)
  )
  (:goal (and
    (not (locked classroom))
    (at alyssa classroom)
    (has alyssa final_exam_paper)
  ))
)