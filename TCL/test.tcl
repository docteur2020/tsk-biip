#!/usr/bin/tclsh

dict set colours  "colour1" "red" 
puts $colours
dict set colours  "colour2" "green"
puts $colours

set colours [dict create colour1 "black" colour2 "white"]
puts $colours

set resultat [ dict get $colours "colour2" ]

puts $resultat