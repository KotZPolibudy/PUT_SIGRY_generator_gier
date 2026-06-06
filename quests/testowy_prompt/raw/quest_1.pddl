(define (problem quest_1)
  (:domain magic-world)
  (:objects
    hero - player
    merchant - npc
    potion - item
    village - location
    tower - location
  )
  (:init
    (at hero village)
    (is-alive hero)
    (npc-wants-item merchant potion)
    (grantable potion)
    (has merchant potion)
    (is-hostile merchant)
    (connected village tower)
  )
  (:goal (and
    (npc-satisfied merchant)
    (has hero potion)
  ))
)