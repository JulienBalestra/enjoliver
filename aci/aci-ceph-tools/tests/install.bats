#!/dgr/bin/bats

@test "rbd is a regular executable file" {
  [ -x "/opt/bin/rbd" ]
}
