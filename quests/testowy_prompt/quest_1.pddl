{
  (:domain magic-world)
  (:objects hero - player merchant - npc potion - item village - location tower - location)
  (:init
    (is-alive hero)
    (is-alive merchant)
    (connected village tower)
    (connected tower village)
    (npc-wants-item merchant potion)
    (grantable potion)
    (has merchant potion)
    (is-hostile merchant)
    (at hero village)
  )
  (:goal (and
    (npc-satisfied merchant)
    (has hero potion)
  ))
}