import threading
from scan_tcp import scan_tcp_devices

thread_detect_ethernet = threading.Thread(target=scan_ethernet_devices, args=(devices, iplist, etherlock,))
thread_detect_ethernet.start()