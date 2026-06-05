(define (problem quest_2)
  (:domain magic-world)
  (:objects
    hero - player
    fire-mage - npc
    ice-spell fire-tome - item
    cave-entrance lava-chamber - location
  )
  (:init
    (at hero cave-entrance)
    (at fire-mage lava-chamber)
    (is-alive hero)
    (is-alive fire-mage)
    (item-at ice-spell cave-entrance)
    (connected cave-entrance lava-chamber)
    (connected lava-chamber cave-entrance)
    (has fire-mage fire-tome)
    (is-weapon ice-spell)
    (vulnerable-to fire-mage ice-spell)
  )
  (:goal (and
    (not (is-alive fire-mage))
    (has hero fire-tome)
  ))
)