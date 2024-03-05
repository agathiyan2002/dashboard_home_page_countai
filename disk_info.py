import psutil

class DiskInfo:
    def __init__(self):
        self.partitions = psutil.disk_partitions(all=True)
        self.root_total = 0
        self.root_used = 0
        self.root_free = 0
        self.home_total = 0
        self.home_used = 0
        self.home_free = 0
        self.get_disk_info()

    def get_disk_info(self):
        for partition in self.partitions:
            if partition.mountpoint == "/":
                root_usage = psutil.disk_usage(partition.mountpoint)
                self.root_total = root_usage.total
                self.root_used = root_usage.used
                self.root_free = root_usage.free
            elif partition.mountpoint == "/home":
                home_usage = psutil.disk_usage(partition.mountpoint)
                self.home_total = home_usage.total
                self.home_used = home_usage.used
                self.home_free = home_usage.free

    def get_root_storage_info(self):
        root_total_gb = self.root_total / (1024 ** 3)
        root_used_gb = self.root_used / (1024 ** 3)
        root_free_gb = self.root_free / (1024 ** 3)
        return {
            "Total storage": root_total_gb,
            "Used storage": root_used_gb,
            "Available storage": root_free_gb
        }

    def get_home_storage_info(self):
        home_total_gb = self.home_total / (1024 ** 3)
        home_used_gb = self.home_used / (1024 ** 3)
        home_free_gb = self.home_free / (1024 ** 3)
        return {
            "Total storage": home_total_gb,
            "Used storage": home_used_gb,
            "Available storage": home_free_gb
        }
