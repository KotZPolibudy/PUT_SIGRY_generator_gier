(define (problem quest_2)
  (:domain magic-world)
  (:objects
    hero - player
    ice-golem - npc
    frost-key - item
    village - location
    merchant-stand - location
    frozen-peak - location
    golem-core - item
  )
  (:init
    (at hero merchant-stand)
    (at ice-golem frozen-peak)
    (is-alive hero)
    (is-alive ice-golem)
    (is-hostile ice-golem)
    (item-at frost-key merchant-stand)
    (connected merchant-stand frozen-peak)
    (connected frozen-peak merchant-stand)
    (item-at golem-core frozen-peak)
    (has ice-golem golem-core)
    (is-weapon frost-key)
    (vulnerable-to ice-golem frost-key)
  )
  (:goal (and
    (not (is-alive ice-golem))
    (has hero golem-core)
  ))
)