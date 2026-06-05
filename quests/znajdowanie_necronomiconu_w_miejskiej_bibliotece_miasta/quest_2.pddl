(define (problem quest_2)
  (:domain magic-world)
  (:objects
    biographer - player
    director - npc
    stun-spray official-stamp - item
    archive-room library-entrance city-square - location
  )
  (:init
    (at biographer archive-room)
    (at director library-entrance)
    (is-alive biographer)
    (is-alive director)
    (is-hostile director)
    (item-at stun-spray archive-room)
    (has director official-stamp)
    (is-weapon stun-spray)
    (vulnerable-to director stun-spray)
    (connected archive-room library-entrance)
    (connected library-entrance archive-room)
    (connected library-entrance city-square)
    (connected city-square library-entrance)
  )
  (:goal (and
    (not (is-alive director))
    (has biographer official-stamp)
    (at biographer city-square)
  ))
)