#!/dgr/bin/bats



@test "Tests are OK" {
  make -C /opt/enjoliver check
  [ $? -eq 0 ]
}

@test "Default config" {
  /opt/enjoliver/manage.py show-config
  [ $? -eq 0 ]
}

@test "validation is OK" {
    /opt/enjoliver/manage.py validate
  [ $? -eq 0 ]
}