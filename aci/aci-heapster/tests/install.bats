#!/dgr/bin/bats

@test "heapster is a regular executable file" {
  [ -x "/usr/bin/heapster" ]
}

#@test "eventer is a regular executable file" {
#  [ -x "/usr/bin/eventer" ]
#}
