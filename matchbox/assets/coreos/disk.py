#!/usr/bin/env python
import argparse
import os.path

READ_ONLY = b'\xff'
READ_WRITE = b'\x00'
MOUNT_OPTION_OFFSET = 0x464 + 3
USER_A = 138412032
FILE_DIR = os.path.dirname(os.path.abspath(__file__))


def change_flag(image_path, read_only=True):
    c = READ_ONLY if read_only else READ_WRITE
    with open(image_path, 'rb+') as f:
        f.seek(USER_A + MOUNT_OPTION_OFFSET)
        f.write(c)


def get_current_flag(image_path):
    with open(image_path, 'rb') as f:
        f.seek(USER_A + MOUNT_OPTION_OFFSET)
        return bytes(f.read(1))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='DiskAlter')
    parser.add_argument('task', type=str, choices=["rw", "ro"],
                        help="Choose the task to run")
    task = parser.parse_args().task
    version = os.getenv("VERSION")
    if not version:
        raise EnvironmentError("VERSION environment variable is not fill")

    image_path = os.path.join(FILE_DIR, version, "coreos_production_image.bin")
    current_flag = get_current_flag(image_path)
    if current_flag != READ_WRITE and current_flag != READ_ONLY:
        raise IOError("%s flag at %d is incoherent: %r ; should be %r or %r" % (
            image_path, USER_A, current_flag, READ_WRITE, READ_ONLY))

    if (current_flag == READ_ONLY and task == "ro") or (current_flag == READ_WRITE and task == "rw"):
        print("Nothing to be done")
        exit(0)

    print("Currently:\n%s: %s" % (image_path, ("ro" if current_flag == READ_ONLY else "rw")))
    change_flag(image_path, True if task == "ro" else False)
    current_flag = get_current_flag(image_path)
    print("End with:\n%s: %s" % (image_path, ("ro" if current_flag == READ_ONLY else "rw")))
