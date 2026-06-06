{
  :domain magic-world
  (:objects alyssa - npc professor - npc textbook - item key1 - item university_building - location hero - character)
  (:init
   (is-alive alyssa) ; Ensure all characters are alive in the init
   (at alyssa university_building)
   (textbook (at professor textbook))
   (is-alive professor)
   (key-for key1 university_building)
   (has professor key1)
   (not (has alyssa textbook)))
  (:goal (and
     (locked university_building)
     (has alyssa textbook))))
}