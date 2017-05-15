#!/dgr/bin/bats


@test "Tests are OK" {
  make -C /opt/enjoliver/app/tests testing.id_rsa
  make -C /opt/enjoliver/app/tests check
  [ $? -eq 0 ]
}

@test "Default config" {
  /opt/enjoliver/manage.py show-configs
  [ $? -eq 0 ]
}

@test "validation is OK" {
    /opt/enjoliver/manage.py validate
  [ $? -eq 0 ]
}