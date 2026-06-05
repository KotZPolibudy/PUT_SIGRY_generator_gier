(define (problem quest_1)
  (:domain magic-world)
  (:objects
    hero - player
    scout - npc
    map volcano-key - item
    village cave-entrance - location
  )
  (:init
    (at hero village)
    (at scout village)
    (is-alive hero)
    (is-alive scout)
    (item-at map village)
    (connected village cave-entrance)
    (connected cave-entrance village)
    (locked cave-entrance)
    (key-for volcano-key cave-entrance)
    (has scout volcano-key)
    (npc-wants-item scout map)
    (grantable volcano-key)
  )
  (:goal (and
    (npc-satisfied scout)
    (at hero cave-entrance)
  ))
)