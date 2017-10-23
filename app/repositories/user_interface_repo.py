import smartdb
import sync
from model import Machine, MachineInterface, Schedule, MachineDisk, MachineCurrentState, LifecycleIgnition, \
    LifecycleRolling


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
            row = dict()

            # Filtering data
            machine_disks = [md for md in mds if md.machine_id == machine.id]
            machine_interfaces = [mi for mi in mis if mi.machine_id == machine.id]

            # MachineInterface
            booting_mac = ""
            for i in mis:
                if i.as_boot is True:
                    machine_interfaces.append(i)
                    booting_mac = i.mac

            machine_states = [ms for ms in mss if ms.machine_mac == booting_mac]
            lifecycle_ignition = [li for li in lis if li.machine_id == machine.id]
            lifecycle_rolling = [lr for lr in lrs if lr.machine_id == machine.id]
            machine_schedules = [sr for sr in srs if sr.machine_id == machine.id]

            # Processing data
            disks = list()
            if machine_disks:
                for disk in machine_disks:
                    disks.append({
                        "path": disk.path,
                        "size-bytes": disk.size
                    })

            # Adding data
            row['LastState'] = machine_states[0].state_name if machine_states else None
            row['FQDN'] = machine_interfaces[0].fqdn if machine_interfaces else None
            row['CIDR'] = machine_interfaces[0].cidrv4 if machine_interfaces else None
            row['MAC'] = machine_interfaces[0].mac if machine_interfaces else None
            row['Roles'] = ",".join([r.role for r in machine_schedules])
            row['DiskProfile'] = sync.ConfigSyncSchedules.compute_disks_size(disks)
            row['LastReport'] = lifecycle_ignition[0].updated_date if lifecycle_ignition else None
            row['UpToDate'] = lifecycle_ignition[0].up_to_date if lifecycle_ignition else None
            row['LastChange'] = lifecycle_ignition[0].last_change_date if lifecycle_ignition else None
            row['UpdateStrategy'] = lifecycle_rolling[0].strategy if lifecycle_rolling and lifecycle_rolling[
                0].enable else "Disable"

            data.append(row)

        return data
