(define (problem quest_3)
  (:domain magic-world)
  (:objects
    hero - player
    gatekeeper king - npc
    fire-tome hot-elixir castle-key - item
    castle-courtyard castle-hall - location
  )
  (:init
    (at hero castle-courtyard)
    (at gatekeeper castle-courtyard)
    (at king castle-hall)
    (is-alive hero)
    (is-alive gatekeeper)
    (is-alive king)
    (has hero fire-tome)
    (item-at hot-elixir castle-courtyard)
    (connected castle-courtyard castle-hall)
    (connected castle-hall castle-courtyard)
    (locked castle-hall)
    (key-for castle-key castle-hall)
    (has gatekeeper castle-key)
    (npc-wants-item gatekeeper hot-elixir)
    (grantable castle-key)
    (npc-wants-item king fire-tome)
  )
  (:goal (and
    (npc-satisfied king)
    (at hero castle-hall)
  ))
)
