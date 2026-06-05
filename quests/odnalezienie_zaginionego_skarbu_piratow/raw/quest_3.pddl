(define (problem quest_3)
  (:domain magic-world)
  (:objects
    hero - player
    treasure_chest_locked - item
    fortress_treasure - location
  )
  (:init
    (at hero island_island_of_enigmas)
    (is-alive hero)
    (has hero ancient_map)
    (key-for ancient_map shipwreck) 
    (item-at treasure_chest_locked fortress_treasure)
  )
  (:goal (and
    (has hero treasure_chest_locked)
  ))
)