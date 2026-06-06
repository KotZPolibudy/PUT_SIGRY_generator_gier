(define (problem quest_2)
  (:domain magic-world)
  (:objects
    hero - player
    relic - item
    village - location
    tower - location
    ancient_treasure - location
  )
  (:init
    (at hero tower)
    (is-alive hero)
    (item-at relic tower)
    (connected tower ancient_treasure)
    (connected ancient_trethere village)
  )
  (:goal (and
    (has hero relic)
    (at hero village)
  ))
)