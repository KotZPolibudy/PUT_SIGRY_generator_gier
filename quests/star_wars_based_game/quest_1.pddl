(define (problem quest_1)
    (:domain magic-world)
    (:objects
        hero - player
        mercenary - npc
        frost-key - item
        village - location
        merchant-stand - location
        frozen-peak - location
    )
    (:init
        (at hero village)
        (at mercenary village)
        (is-alive hero)
        (is-alive mercenary)
        (item-at frost-key merchant-stand)
        (connected village merchant-stand)
        (connected merchant-stand village)
        (locked frozen-peak)
        (key-for frost-key frozen-peak)
        (has mercenary frost-key)
    )
    (:goal
        (and (has hero frost-key))
    )
)