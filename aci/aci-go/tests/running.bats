#!/dgr/bin/bats


@test "Go is here" {
  /usr/bin/go version
  [ $? -eq 0 ]
}

