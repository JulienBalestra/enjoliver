#!/dgr/bin/bats

@test "nerve is well installed" {
  [ -x /usr/bin/nerve ]
}

