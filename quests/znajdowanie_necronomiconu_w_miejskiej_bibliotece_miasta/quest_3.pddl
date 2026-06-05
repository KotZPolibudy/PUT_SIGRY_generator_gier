(define (problem quest_3)
  (:domain magic-world)
  (:objects
    biographer - player
    clerk mayor - npc
    necronomicon official-stamp town-hall-key - item
    city-square town-hall mayors-office - location
  )
  (:init
    (at biographer city-square)
    (at clerk city-square)
    (at mayor mayors-office)
    (is-alive biographer)
    (is-alive clerk)
    (is-alive mayor)
    (has biographer necronomicon)
    (has biographer official-stamp)
    (connected city-square town-hall)
    (connected town-hall city-square)
    (connected town-hall mayors-office)
    (connected mayors-office town-hall)
    (locked town-hall)
    (key-for town-hall-key town-hall)
    (has clerk town-hall-key)
    (npc-wants-item clerk official-stamp)
    (grantable town-hall-key)
    (npc-wants-item mayor necronomicon)
  )
  (:goal (and
    (npc-satisfied mayor)
    (at biographer mayors-office)
  ))
)