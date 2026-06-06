(define (problem quest_3)
    (:domain magic-world)
    (:objects
        hero - player
        treasure_guard - npc
        treasure_chest_locked - item
        ancient_map - item
        shipwreck_key - item
        island_of_enigmas - location
        shipwreck - location
        fortress_tre_zz - location
    )
    (:init
        (at hero island_of_enigmas)
        (is-alive hero)
        (is-alive treasure_guard)
        (at treasure_guard fortress_tre_zz)
        (has hero ancient_map)
        (item-at shipwreck_key shipwreck)
        (item-at treasure_chest_locked fortress_tre_zz)
        (connected island_of_enigmas shipwreck)
        (connected shipwreck island_of_enigmas)
        (connected shipwreck fortress_tre_zz)
        (connected fortress_tre_zz shipwreck)
        (locked fortress_tre_zz)
        (key-for shipwreck_key fortress_tre_zz)
    )
    (:goal
        (and (has hero treasure_chest_locked))
    )
)