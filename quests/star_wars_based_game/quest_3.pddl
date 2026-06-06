(define (problem quest_3)
    (:domain magic-world)
    (:objects
        hero - player
        start - location
        cave - location
        sanctuary - location
        relic - item
        ancient-key - item
        goblin - npc
        priest - npc
    )
    (:init
        (at hero start)
        (is-alive hero)
        (is-alive goblin)
        (is-alive priest)
        (item-at relic cave)
        (item-at ancient-key sanctuary)
        (has goblin ancient-key)
        (has priest relic)
        (at goblin cave)
        (at priest sanctuary)
        (at start start)
        (connected start cave)
        (connected cave sanctuary)
        (key-for ancient-key sanctuary)
        (vulnerable-to goblin relic)
        (grantable relic)
        (npc-wants-item priest relic)
        (connected sanctuary cave)
        (connected cave start)
    )
    (:goal
        (and (at hero sanctuary) (has hero relic))
    )
)