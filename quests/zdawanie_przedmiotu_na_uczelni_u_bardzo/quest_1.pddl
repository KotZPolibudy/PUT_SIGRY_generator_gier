(define (problem quest_1)
  (:domain magic-world)
  (:objects
    hero - player
    professor - npc
    textbook - item
    corridor - location
    classroom - location
  )
  (:init
    (at hero corridor)
    (at professor corridor)
    (is-alive hero)
    (is-alive professor)
    (item-at textbook corridor)
    (connected corridor classroom)
    (connected classroom corridor)
    (locked classroom)
    (key-for textbook classroom)
    (npc-wants-item professor textbook)
    (grantable textbook)
  )
  (:goal (and
    (has-talked hero professor)
    (npc-satisfied professor)
  ))
)