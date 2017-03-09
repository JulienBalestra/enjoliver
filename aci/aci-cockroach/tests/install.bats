#!/dgr/bin/bats

@test "cockroach is well installed" {
  [ -x /usr/bin/cockroach ]
}

