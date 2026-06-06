(define (problem quest_2)
  (:domain magic-world)
  (:objects
    alyssa - player
    professor - npc
    key2 - item
    classroom - location
  )
  (:init
    (at alyssa university_building)
    (is-alive alyssa)
    (is-alive professor)
    (locked classroom)
    (key-for key2 classroom)
    (has professor key2)
  )
  (:goal (and
    (not (locked classroom))
    (at alyssa classroom)
  ))
)