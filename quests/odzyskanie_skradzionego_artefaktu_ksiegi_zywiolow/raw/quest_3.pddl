(define (problem quest_3)
  (:domain magic-world)
  (:objects
    player - character
    mage - character
    frozen-king - item
    village - location
    castle - location
  )
  (:init
    (is-alive player) ; Ensure the player is alive at initialization
    (at player village)
    (not (is-hostile mage))
    (item-at frozen-king castle)
    (at mage cave)
    (locked-castle-door)
    (key-for magic-key castle)
  )
  (:goal
    (and
      (not (is-hostile mage)) ; Ensure mage is not hostile at goal
      (at player village) ; Player should still be in the village at goal
      (freezed-king-freeed frozen-king) ; Assume a condition for freed king, may vary based on actual logic
    ))
)
