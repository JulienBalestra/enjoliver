import copy

from sqlalchemy.orm import joinedload

import smartdb
import sync
from model import Machine, MachineInterface, Schedule, MachineDisk, MachineCurrentState, LifecycleIgnition, LifecycleRolling


class UserInterfaceRepository:
    """
    Get the data for the User Interface View
    """

    def __init__(self, smart: smartdb.SmartDatabaseClient):
        self.smart = smart

    def get_machines_overview(self):
        """
        TODO refactor this ugly stuff
        :return:
        """
        with self.smart.new_session() as session:
            # Fetching data
            mis = session.query(MachineInterface).filter(MachineInterface.as_boot == True).all()
            mds = session.query(MachineDisk).all()
            mss = session.query(MachineCurrentState).all()
            lis = session.query(LifecycleIgnition).all()
            lrs = session.query(LifecycleRolling).all()
            srs = session.query(Schedule).all()

        data = list()
        for machine in session.query(Machine):
            row = {}

            # Filtering data
            md = [md for md in mds if md.machine_id == machine.id]
            mi = [mi for mi in mis if mi.machine_id == machine.id]
            ms = [ms for ms in mss if ms.machine_id == machine.id]
            li = [li for li in lis if li.machine_id == machine.id]
            lr = [lr for lr in lrs if lr.machine_id == machine.id]
            sr = [sr for sr in srs if sr.machine_id == machine.id]

            # Processing data
            disks = list()
            if md:
                for disk in md:
                    disks.append({
                        "path": disk.path,
                        "size-bytes": disk.size
                    })

            # Adding data
            row['LastState'] = ms[0].state_name if ms else None
            row['FQDN'] = mi[0].fqdn if mi else None
            row['CIDR'] = mi[0].cidrv4 if mi else None
            row['MAC'] = mi[0].mac if mi else None
            row['Roles'] = ",".join([r.role for r in sr])
            row['DiskProfile'] = sync.ConfigSyncSchedules.compute_disks_size(disks)
            row['LastReport'] = li[0].updated_date if li else None
            row['UpToDate'] = li[0].up_to_date if li else None
            row['LastChange'] = li[0].last_change_date if li else None
            row['UpdateStrategy'] = lr[0].strategy if lr and lr[0].enable else "Disable"

            data.append(row)

        return data
