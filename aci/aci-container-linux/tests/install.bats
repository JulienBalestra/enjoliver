#!/dgr/bin/bats

@test "is well installed" {
  [ -x /usr/bin/make ]
  [ -x /usr/bin/unsquashfs ]
  [ -x /usr/bin/cgpt ]
  [ -x /sbin/losetup ]
  [ -x /bin/bzip2 ]
  [ -x /bin/cpio ]
}

