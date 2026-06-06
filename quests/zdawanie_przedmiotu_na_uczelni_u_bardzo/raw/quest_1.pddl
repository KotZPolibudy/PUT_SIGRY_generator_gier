(define (problem quest_1)
  (:domain magic-world)
  (:objects
    alyssa - player
    professor - npc
    textbook - item
    key1 - item
    university_building - location
  )
  (:init
    (at alyssa university_building)
    (is-alive alyssa)
    (is-alive professor)
    (locked university_building)
    (key-for key1 university_building)
    (has professor key1)
  )
  (:goal (and
    (not (locked university_building))
    (has alyssa textbook)
  ))
)