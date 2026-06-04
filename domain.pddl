(define (domain magic-world)
    (:requirements :strips :typing)
    
    (:types
        location character item - object
        player npc - character
    )

    (:predicates
        (at ?c - character ?l - location)
        (connected ?l1 - location ?l2 - location)
        
        (explored ?l - location)
        (locked ?l - location)
        (key-for ?i - item ?l - location)

        (item-at ?i - item ?l - location)
        (has ?c - character ?i - item)
        
        (grantable ?i - item)
        (is-weapon ?i - item)
        (is-alive ?c - character)
        (vulnerable-to ?c - character ?i - item)

        (has-talked ?p - player ?n - npc)
        (npc-wants-item ?n - npc ?i - item)
        (npc-satisfied ?n - npc)
        (is-hostile ?c - character)
    )

    (:action scout
        :parameters (?p - player ?from - location ?to - location)
        :precondition (and 
            (at ?p ?from)
            (connected ?from ?to)
            (not (explored ?to))
        )
        :effect (explored ?to)
    )

    (:action unlock
        :parameters (?p - player ?from - location ?to - location ?k - item)
        :precondition (and
            (at ?p ?from)
            (connected ?from ?to)
            (explored ?to)
            (locked ?to)
            (has ?p ?k)
            (key-for ?k ?to)
        )
        :effect (and
            (not (locked ?to))
        )
    )

    (:action move
        :parameters (?p - player ?from - location ?to - location)
        :precondition (and
            (at ?p ?from)
            (connected ?from ?to)
            (explored ?to)
            (not (locked ?to))
        )
        :effect (and
            (not (at ?p ?from))
            (at ?p ?to)
        )
    )


    (:action pick-up
        :parameters (?p - player ?i - item ?l - location)
        :precondition (and
            (at ?p ?l)
            (item-at ?i ?l)
        )
        :effect (and
            (not (item-at ?i ?l))
            (has ?p ?i)
        )
    )

    (:action loot
        :parameters (?p - player ?c - character ?i - item ?l - location)
        :precondition (and
            (at ?p ?l)
            (at ?c ?l)
            (not (is-alive ?c))
            (has ?c ?i)
        )
        :effect (and
            (not (has ?c ?i))
            (has ?p ?i)
        )
    )

    (:action talk
        :parameters (?p - player ?n - npc ?l - location)
        :precondition (and
            (at ?p ?l)
            (at ?n ?l)
            (is-alive ?n)
            (not (is-hostile ?n))
        )
        :effect (has-talked ?p ?n)
    )

    (:action give-item
        :parameters (?p - player ?n - npc ?i - item ?l - location)
        :precondition (and
            (at ?p ?l)
            (at ?n ?l)
            (has ?p ?i)
            (npc-wants-item ?n ?i)
            (is-alive ?n)
            (has-talked ?p ?n)
        )
        :effect (and
            (not (has ?p ?i))
            (has ?n ?i)
            (npc-satisfied ?n)
        )
    )

    (:action receive-item
        :parameters (?p - player ?n - npc ?i - item ?l - location)
        :precondition (and
            (at ?p ?l)
            (at ?n ?l)
            (is-alive ?n)
            (has-talked ?p ?n)
            (not (is-hostile ?n))
            (grantable ?i)
            (has ?n ?i)
        )
        :effect (and
            (not (has ?n ?i))
            (has ?p ?i)
        )
    )

    (:action steal
        :parameters (?p - player ?n - npc ?i - item ?l - location)
        :precondition (and
            (at ?p ?l)
            (at ?n ?l)
            (is-alive ?n)
            (not (is-hostile ?n))
            (not (grantable ?i))
            (has ?n ?i)
        )
        :effect (and
            (not (has ?n ?i))
            (has ?p ?i)
            (is-hostile ?n)
        )
    )

    (:action kill
        :parameters (?p - player ?c - character ?l - location ?w - item)
        :precondition (and
            (at ?p ?l)
            (at ?c ?l)
            (has ?p ?w)
            (is-weapon ?w)
            (vulnerable-to ?c ?w)
            (is-alive ?c)
            (is-alive ?p)
        )
        :effect (not (is-alive ?c))
    )
)