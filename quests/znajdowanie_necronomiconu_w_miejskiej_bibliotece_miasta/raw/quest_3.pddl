(define (problem return_necronomicon)
 (:domain magic-world)
 (:objects
   biographer - player
 )
 (:init
   (at biographer library)
   (is-alive biographer)
   (has necronomicon) 
 )
 (:goal (and
   (not (locked library))
 ))
)