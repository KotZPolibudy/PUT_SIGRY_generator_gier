(define (problem search_necronomicon)
 (:domain magic-world)
 (:objects
   biographer - player
   librarian - npc
   necronomicon - item
 )
 (:init
   (at biographer library)
   (is-alive biographer)
   (is-alive librarian)
   (locked library)
   (key-for key-necronomicon library)
   (has librarian key-necronomicon)
   (npc-wants-item librarian necronomicon)
 )
 (:goal (and
   (not (locked library))
   (has biographer necronomicon)
 ))
)