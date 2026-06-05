(define (problem quest_2)
  (:domain magic-world)
  (:objects
    player - character,
    mage - character,
    zombified-creature - item,
    village - location,
    cave - location
  )
  (:init
    (is-alive player) 
    (at player village)
    (not (is-hostile mage))
    (has-player zombified-creature)
    (item-at zombified-creature village)
    (at mage cave)
    (locked cave)
    (key-for magic-key cave)
  )
  (:goal (and
    (not (is-hostile mage))
    (at player village)
  ))
)