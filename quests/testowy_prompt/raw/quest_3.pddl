(define (problem quest_3)
  (:domain magic-world)
  (:objects
    hero - player
    relic - item
    village - location
    ancient_trethere - location
  )
  (:init
    (at hero village)
    (is-alive hero)
    (has relic hero)
    (connected ancient_trethere village)
  )
  (:goal (and
    (npc-satisfied relic_guardian)
    (not (is-hostile relic_guardian))
  ))
)