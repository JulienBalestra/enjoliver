import copy

from sqlalchemy.orm import joinedload

import smartdb
import sync
from model import Machine, MachineInterface


class UserInterfaceRepository:
    """
    Get the data for the User Interface View
    """
    vuejs_data = {
        "gridColumns": [
            "MAC",
            "CIDR",
            "FQDN",
            "DiskProfile",
            "Roles",
            "LastState",
            "UpdateStrategy",
            "UpToDate",
            "LastReport",
            "LastChange",
        ],
        "gridData": []
    }

    def __init__(self, smart: smartdb.SmartDatabaseClient):
        self.smart = smart

    def get_machines_overview(self):
        """
        TODO refactor this ugly stuff
        :return:
        """
        data = copy.deepcopy(self.vuejs_data)
        with self.smart.new_session() as session:
            for machine in session.query(Machine) \
                    .options(joinedload("interfaces")) \
                    .options(joinedload("lifecycle_ignition")) \
                    .options(joinedload("schedules")) \
                    .options(joinedload("disks")) \
                    .options(joinedload("machine_state")) \
                    .options(joinedload("lifecycle_rolling")) \
                    .filter(MachineInterface.as_boot == True):

                last_state = machine.machine_state[0].state_name if machine.machine_state else None
                lifecycle_rolling = machine.lifecycle_rolling[0].strategy if machine.lifecycle_rolling else "Disable"

                if machine.lifecycle_ignition:
                    ignition_updated_date = machine.lifecycle_ignition[0].updated_date
                    ignition_up_to_date = machine.lifecycle_ignition[0].up_to_date
                    ignition_last_change = machine.lifecycle_ignition[0].last_change_date
                else:
                    ignition_updated_date, ignition_up_to_date, ignition_last_change = None, None, None

                disks = list()
                if machine.disks:
                    for disk in machine.disks:
                        disks.append({
                            "path": disk.path,
                            "size-bytes": disk.size
                        })
                row = {
                    "Roles": ",".join([r.role for r in machine.schedules]),
                    "FQDN": machine.interfaces[0].fqdn,
                    "CIDR": machine.interfaces[0].cidrv4,
                    "MAC": machine.interfaces[0].mac,
                    "LastState": last_state,
                    "LastReport": ignition_updated_date,
                    "LastChange": ignition_last_change,
                    "UpToDate": ignition_up_to_date,
                    "UpdateStrategy": lifecycle_rolling,
                    "DiskProfile": sync.ConfigSyncSchedules.compute_disks_size(disks)
                }
                data["gridData"].append(row)

        return data
