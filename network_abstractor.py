import socket
import json
import sys
from threading import Thread


class NetworkAbstractorServer(object):
    def __init__(self, game_host, game_port, serv_host="127.0.0.1", serv_port=23232):
        self.server = socket.socket()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((serv_host, serv_port))
        self.server.listen(5)
        print("Listening for ais on: " + serv_host + ":" + str(serv_port))
        
        self.game_host = game_host
        self.game_port = game_port
        
        self.running = True
        self.connections = []
        self.abstract_connections = {}
        self.matching = {}
        
        t = Thread(target=self.accept)
        t.setDaemon(True)
        t.start()
        
    def accept(self):
        while self.running:
            (sock, addr) = self.server.accept()
            self.connections.append(sock)
            t = Thread(target=self.connection, args=(sock,))
            t.setDaemon(True)
            t.start()
            
    def connection(self, sock):
        sf = sock.makefile()
        name = None
        print("Opened connection")
        while self.running:
            try:
                line = sf.readline().rstrip('\n')
                event = {"packet": json.loads(line), "sock": sock}
                if "name" in event["packet"]:
                    name = event["packet"]["name"]
                    self.matching[name] = sock
                    print("Attached connection to: " + name)
                    if not name in self.abstract_connections:
                        s = socket.socket()
                        s.connect((self.game_host, self.game_port))
                        self.connections.append(s)
                        s.send(json.dumps({"name": name}) + "\n")
                        self.abstract_connections[name] = s
                        
                        t = Thread(target=self.connection_inverse, args=(s, name))
                        t.setDaemon(True)
                        t.start()
                elif name is not None:
                    self.abstract_connections[name].send(line + "\n")
            except:
                break
        if name is not None:
            del self.matching[name]
        try:
            sock.close()
        except:
            print("Cannot close socket.", sys.exc_info()[0])
        
        self.connections.remove(sock)
        
        if name is None:
            name = "unknown"
        print("Terminated connection for: " + name)
        
    def connection_inverse(self, sock, name):
        print("Started inverse connection for: " + name)
        sf = sock.makefile()
        while self.running:
            try:
                line = sf.readline().rstrip('\n')                    
                if name in self.matching:
                    self.matching[name].send(line + "\n")
                    
                if line == "":
                    break
            except:
                print("Unexpected error:", sys.exc_info()[0])
                break
        del self.abstract_connections[name]
        try:
            sock.close()
        except:
            print("Cannot close socket.", sys.exc_info()[0])
        
        print("Terminated inverse connection for: " + name)
        if name in self.matching:
            self.matching[name].close()
        self.connections.remove(sock)
        
    def quit(self):
        self.running = False
        self.server.close()
        for conn in self.connections:
            conn.close()
            
if len(sys.argv) == 3:
    NetworkAbstractorServer(sys.argv[1], int(sys.argv[2]))
    try:
        input("Press enter to continue")
    except SyntaxError:
        pass
else:
    print("Usage: python network_abstractor.py <host> <port>")