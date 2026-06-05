(define (problem quest_1)
 (:domain magic-world)
 (:objects
 player - character
 mage - character
 tome - item
 village - location
 cave - location
 )
 (:init
 (is-alive player)
 (is-alive mage)
 (at player village)
 (item-at tome cave)
 (has-player tome)  ; Fix: Change to have-tome instead of has-player item-to-steal
 (not (at player cave))
 )
 (:goal
 (and
 (is-alive player)
 (at player village)
 (not (at mage cave))
 ))
 )