(define (problem fight_for_necronomicon)
 (:domain magic-world)
 (:objects
   biographer - player
   corrupt_officials - character
 )
 (:init
   (at biographer library)
   (is-alive biographer)
   (is-alive corrupt_officials)
   (locked office_building)
   (key-for key-office_office corrent_building)
   (has corrupt_officials key-office_office)
 )
 (:goal (and
   (not (locked library))
   (npc-satisfied corrupt_officials) 
 ))
)