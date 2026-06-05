(define (problem quest_1)
  (:domain magic-world)
  (:objects
    biographer - player
    archivist - npc
    permit archive-key necronomicon - item
    library-entrance archive-room - location
  )
  (:init
    (at biographer library-entrance)
    (at archivist library-entrance)
    (is-alive biographer)
    (is-alive archivist)
    (item-at permit library-entrance)
    (item-at necronomicon archive-room)
    (connected library-entrance archive-room)
    (connected archive-room library-entrance)
    (locked archive-room)
    (key-for archive-key archive-room)
    (has archivist archive-key)
    (npc-wants-item archivist permit)
    (grantable archive-key)
  )
  (:goal (and
    (npc-satisfied archivist)
    (has biographer necronomicon)
  ))
)