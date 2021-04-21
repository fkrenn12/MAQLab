import psutil
import os
import sys
import time


# ----------------------
# cleanup temp folder
# ----------------------
def cleanup_mei():
    """
    Rudimentary workaround for https://github.com/pyinstaller/pyinstaller/issues/2379
    """
    import sys
    import os
    from shutil import rmtree

    mei_bundle = getattr(sys, "_MEIPASS", False)

    if mei_bundle:
        dir_mei, current_mei = mei_bundle.split("_MEI")
        for file in os.listdir(dir_mei):
            if file.startswith("_MEI") and not file.endswith(current_mei):
                try:
                    rmtree(os.path.join(dir_mei, file))
                except PermissionError:  # mainly to allow simultaneous pyinstaller instances
                    pass


# ----------------------
# removing old log file
# ----------------------
def remove_log_file():
    try:
        if os.path.isfile("../log_provider.txt"):
            os.remove("../log_provider.txt")
    except:
        pass


# -----------------------------------------------------------------
#  Clear the console
# -----------------------------------------------------------------
def console_clear():
    os.system("cls\n")


# -----------------------------------------------------------------
#  Create the restart cmd script in the curent working dir
# -----------------------------------------------------------------
def create_restart_cmd():
    p = psutil.Process(os.getpid())
    # name = p.name().split(".")[0]
    name = "restart_" + p.name().split(".")[0] + ".cmd"
    f = open(name, "w")
    f.write("TASKKILL /F /IM " + p.name() + "\n")
    f.write("start " + p.name())
    f.close()


# -----------------------------------------------------------------
#  LOAD of CPU
# -----------------------------------------------------------------
def cpu_load():
    number_of_cpu = psutil.cpu_count()
    x = psutil.cpu_percent(percpu=True)
    total = 0
    for procent in x:
        total += procent
    cpu_load_avg = round(total / number_of_cpu * 2, 1)
    if cpu_load_avg > 100:
        cpu_load_avg = 100
    cpu_load_max = round(max(x), 1)
    return (cpu_load_max + cpu_load_avg) / 2.0


# -----------------------------------------------------------------
#  R E S T A R T
# -----------------------------------------------------------------
def restart():
    p = psutil.Process(os.getpid())
    name = "restart_" + p.name().split(".")[0] + ".cmd"
    if "python.exe" not in p.name():
        # this is an executable
        os.system(name)
        # os.execl(python, python, *sys.argv)
    else:
        # this is a script
        print("SCRIPT Restarting...")
        try:
            # restarting the script is not working in pycharm
            # restarting script is not tested yet outside pycharm
            os.execv(__file__, sys.argv)
        except:
            print("SCRIPT Restarting failed...")


# -----------------------------------------------------------------
#  T E R M I N A T E
# -----------------------------------------------------------------
def terminate():
    p = psutil.Process(os.getpid())
    os.system("TASKKILL /F /IM " + p.name())


# -----------------------------------------------------------------
#  S H U T D O W N
# -----------------------------------------------------------------
def shutdown_server(servers=None):
    if servers is not None and type(servers) is tuple:
        for server in servers:
            try:
                server.stop_request = True
                time.sleep(10)
                del server
            except:
                pass
