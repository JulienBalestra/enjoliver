#!/dgr/bin/bats

@test "tiller is a regular executable file" {
  [ -x "/usr/bin/tiller" ]
}
