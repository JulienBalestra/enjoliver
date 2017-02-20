#!/dgr/bin/bats


@test "Tests are OK" {
  make -C /opt/enjoliver check
  [ $? -eq 0 ]
}

@test "validation is OK" {
    /opt/enjoliver/manage.py validate
  [ $? -eq 0 ]
}