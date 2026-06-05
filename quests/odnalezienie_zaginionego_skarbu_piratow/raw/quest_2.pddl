(define (problem quest_2)
  (:domain magic-world)
  (:objects
    hero - player
    island_island_of_enigmas - location
    ancient_map - item
    treasure_chest_unlocked - item
  )
  (:init
    (at hero village)
    (is-alive hero)
    (connected shipwreck island_island_of_enigmas)
    (has hero ancient_map)
    (key-for ancient_map shipwreck) 
    (item-at treasure_chest_unlocked island_island_of_enigmas)
  )
  (:goal (and
    (has hero treasure_chest_unlocked)
  ))
)