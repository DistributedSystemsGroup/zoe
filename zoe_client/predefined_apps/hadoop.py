from common.application_description import ZoeProcessEndpoint, ZoeApplicationProcess, ZoeApplication


def hadoop_namenode_proc(image: str) -> ZoeApplicationProcess:
    proc = ZoeApplicationProcess()
    proc.name = "hdfs-namenode"
    proc.docker_image = image
    proc.monitor = True
    proc.required_resources["memory"] = 2 * 1024 * 1024 * 1024  # 2 GB
    port = ZoeProcessEndpoint()
    port.name = "NameNode web interface"
    port.protocol = "http"
    port.port_number = 50070
    port.path = "/"
    port.is_main_endpoint = True
    proc.ports.append(port)
    proc.environment.append(["NAMENODE_HOST", "hdfs-namenode-{execution_id}"])
    return proc


def hadoop_datanode_proc(count: int, image: str) -> list:
    ret = []
    for i in range(count):
        proc = ZoeApplicationProcess()
        proc.name = "hdfs-datanode-{}".format(i)
        proc.docker_image = image
        proc.monitor = False
        proc.required_resources["memory"] = 1 * 1024 * 1024 * 1024  # 1 GB
        proc.environment.append(["NAMENODE_HOST", "hdfs-namenode-{execution_id}"])
        ret.append(proc)
    return ret


def hdfs_app(name: str, namenode_image: str, datanode_count: int, datanode_image: str):
    app = ZoeApplication()
    app.name = name
    app.will_end = False
    app.priority = 512
    app.requires_binary = False
    namenode = hadoop_namenode_proc(namenode_image)
    app.processes.append(namenode)
    datanodes = hadoop_datanode_proc(datanode_count, datanode_image)
    app.processes += datanodes
    return app
