(define (problem quest_1)
    (:domain magic-world)
    (:objects
        hero - player
        pirate_captain - npc
        treasure_chest - item
        shipwreck - location
        village - location
    )
    (:init
        (at hero village)
        (is-alive hero)
        (item-at treasure_chest shipwreck)
        (connected village shipwreck)
        (is-alive pirate_captain)
        (connected shipwreck village)
    )
    (:goal
        (and (has hero treasure_chest))
    )
)