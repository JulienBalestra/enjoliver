#!/dgr/bin/bats

@test "vault is well installed" {
  [ -x /usr/bin/vault ]
}

