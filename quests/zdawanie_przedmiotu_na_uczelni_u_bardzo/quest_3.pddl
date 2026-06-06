(define (problem quest_3)
  (:domain magic-world)
  (:objects
    hero - player
    professor - npc
    project-report - item
    deans-office - location
    seminar-room - location
  )
  (:init
    (at hero deans-office)
    (at professor seminar-room)
    (is-alive hero)
    (is-alive professor)
    (item-at project-report deans-office)
    (connected deans-office seminar-room)
    (connected seminar-room deans-office)
    (npc-wants-item professor project-report)
    (grantable project-report)
  )
  (:goal (and
    (has-talked hero professor)
    (npc-satisfied professor)
  ))
)