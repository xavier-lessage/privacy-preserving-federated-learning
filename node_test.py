from time import sleep

from PROJH402.TCP.Connections import *

node0 = NodeThread("", 65434, 65336)
node1 = NodeThread("", 65435, 65337)
node2 = NodeThread("", 65436, 65338)

node0.start()
node1.start()
node2.start()


node0.connect_to("127.0.0.1", 65436)
node0.connect_to("127.0.0.1", 65435)
# node0.network_send("Hello")


def node_connect():
    sleep(2)
    print("Node 0: ", len(node0.nodes_connected))
    print("Node 1: ", len(node1.nodes_connected))
    print("Node 2: ", len(node2.nodes_connected))


if __name__ == '__main__':
    node_connect()
    node0.stop()
    node1.stop()
    node2.stop()
