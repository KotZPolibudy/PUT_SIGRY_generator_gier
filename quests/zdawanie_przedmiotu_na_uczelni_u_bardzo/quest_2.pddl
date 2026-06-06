(define (problem quest_2)
  (:domain magic-world)
  (:objects
    hero - player
    professor - npc
    secretary - npc
    stamped-form - item
    office-key - item
    hallway - location
    deans-office - location
  )
  (:init
    (at hero hallway)
    (at secretary hallway)
    (at professor deans-office)
    (is-alive hero)
    (is-alive secretary)
    (is-alive professor)
    (item-at stamped-form hallway)
    (connected hallway deans-office)
    (connected deans-office hallway)
    (locked deans-office)
    (key-for office-key deans-office)
    (has secretary office-key)
    (npc-wants-item secretary stamped-form)
    (grantable office-key)
  )
  (:goal (and
    (npc-satisfied secretary)
    (has hero office-key)
    (at hero deans-office)
  ))
)