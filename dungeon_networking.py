import socket
import threading
import json
import pickle
from enum import Enum


class MessageType(Enum):
    PLAYER_UPDATE = "player_update"
    BLOCK_PLACE = "block_place"
    BLOCK_REMOVE = "block_remove"
    DUNGEON_DATA = "dungeon_data"
    PLAYER_JOIN = "player_join"
    PLAYER_LEAVE = "player_leave"
    GAME_STATE = "game_state"
    DAMAGE = "damage"
    CHAT = "chat"


class NetworkServer:
    def __init__(self, host='0.0.0.0', port=5555, max_players=4):
        self.host = host
        self.port = port
        self.max_players = max_players
        self.server_socket = None
        self.clients = {}  # {addr: {'socket': socket, 'player_id': id, 'role': role}}
        self.running = False
        self.game_state = {
            'players': {},
            'blocks': [],  # Builder-placed blocks
            'dungeon': None,
            'enemies': []
        }
        
    def start(self):
        """Start the server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.max_players)
        self.running = True
        
        print(f"Server started on {self.host}:{self.port}")
        
        # Start accepting connections
        accept_thread = threading.Thread(target=self._accept_connections)
        accept_thread.daemon = True
        accept_thread.start()
        
    def stop(self):
        """Stop the server"""
        self.running = False
        for client_data in self.clients.values():
            client_data['socket'].close()
        if self.server_socket:
            self.server_socket.close()
        print("Server stopped")
        
    def _accept_connections(self):
        """Accept incoming client connections"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                if len(self.clients) < self.max_players:
                    print(f"New connection from {addr}")
                    self.clients[addr] = {
                        'socket': client_socket,
                        'player_id': f"player_{len(self.clients)}",
                        'role': None
                    }
                    
                    # Start thread to handle this client
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                else:
                    client_socket.close()
            except:
                break
                
    def _handle_client(self, client_socket, addr):
        """Handle messages from a client"""
        try:
            while self.running:
                data = self._recv_data(client_socket)
                if not data:
                    break
                    
                msg = json.loads(data)
                self._process_message(msg, addr)
                
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            self._remove_client(addr)
            
    def _process_message(self, msg, addr):
        """Process received message and broadcast if needed"""
        msg_type = msg.get('type')
        
        if msg_type == MessageType.PLAYER_UPDATE.value:
            # Update player position and broadcast
            player_id = self.clients[addr]['player_id']
            self.game_state['players'][player_id] = msg['data']
            self.broadcast(msg, exclude_addr=addr)
            
        elif msg_type == MessageType.BLOCK_PLACE.value:
            # Builder placed a block - sync to all clients
            block = msg['data']
            self.game_state['blocks'].append(block)
            self.broadcast(msg)
            
        elif msg_type == MessageType.BLOCK_REMOVE.value:
            # Remove block and sync
            block_pos = tuple(msg['data'])
            self.game_state['blocks'] = [
                b for b in self.game_state['blocks'] 
                if (b['x'], b['y']) != block_pos
            ]
            self.broadcast(msg)
            
        elif msg_type == MessageType.PLAYER_JOIN.value:
            # New player joined - send them the current game state
            player_id = self.clients[addr]['player_id']
            self.clients[addr]['role'] = msg['data']['role']
            
            # Send full game state to new player
            state_msg = {
                'type': MessageType.GAME_STATE.value,
                'data': {
                    'player_id': player_id,
                    'game_state': self.game_state
                }
            }
            self._send_data(self.clients[addr]['socket'], json.dumps(state_msg))
            
            # Notify others
            join_msg = {
                'type': MessageType.PLAYER_JOIN.value,
                'data': {
                    'player_id': player_id,
                    'role': msg['data']['role']
                }
            }
            self.broadcast(join_msg, exclude_addr=addr)
            
    def broadcast(self, msg, exclude_addr=None):
        """Send message to all connected clients"""
        data = json.dumps(msg)
        for addr, client_data in list(self.clients.items()):
            if addr != exclude_addr:
                try:
                    self._send_data(client_data['socket'], data)
                except:
                    self._remove_client(addr)
                    
    def _remove_client(self, addr):
        """Remove disconnected client"""
        if addr in self.clients:
            player_id = self.clients[addr]['player_id']
            del self.clients[addr]
            
            # Remove from game state
            if player_id in self.game_state['players']:
                del self.game_state['players'][player_id]
            
            # Notify others
            leave_msg = {
                'type': MessageType.PLAYER_LEAVE.value,
                'data': {'player_id': player_id}
            }
            self.broadcast(leave_msg)
            print(f"Client {addr} disconnected")
            
    def _send_data(self, sock, data):
        """Send length-prefixed data"""
        data_bytes = data.encode('utf-8')
        length = len(data_bytes).to_bytes(4, 'big')
        sock.sendall(length + data_bytes)
        
    def _recv_data(self, sock):
        """Receive length-prefixed data"""
        length_bytes = self._recv_all(sock, 4)
        if not length_bytes:
            return None
        length = int.from_bytes(length_bytes, 'big')
        return self._recv_all(sock, length).decode('utf-8')
        
    def _recv_all(self, sock, n):
        """Receive exactly n bytes"""
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return bytes(data)


class NetworkClient:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.player_id = None
        self.message_handlers = {}
        
    def connect(self, role):
        """Connect to server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Send join message
            join_msg = {
                'type': MessageType.PLAYER_JOIN.value,
                'data': {'role': role}
            }
            self.send_message(join_msg)
            
            # Start receive thread
            recv_thread = threading.Thread(target=self._receive_loop)
            recv_thread.daemon = True
            recv_thread.start()
            
            print(f"Connected to server at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from server"""
        self.connected = False
        if self.socket:
            self.socket.close()
            
    def send_message(self, msg):
        """Send message to server"""
        if not self.connected:
            return
        try:
            data = json.dumps(msg)
            self._send_data(data)
        except Exception as e:
            print(f"Send error: {e}")
            self.connected = False
            
    def register_handler(self, msg_type, handler):
        """Register a handler for a message type"""
        self.message_handlers[msg_type] = handler
        
    def _receive_loop(self):
        """Continuously receive messages from server"""
        while self.connected:
            try:
                data = self._recv_data()
                if not data:
                    break
                    
                msg = json.loads(data)
                msg_type = msg.get('type')
                
                # Call registered handler if exists
                if msg_type in self.message_handlers:
                    self.message_handlers[msg_type](msg['data'])
                    
            except Exception as e:
                print(f"Receive error: {e}")
                break
                
        self.connected = False
        print("Disconnected from server")
        
    def _send_data(self, data):
        """Send length-prefixed data"""
        data_bytes = data.encode('utf-8')
        length = len(data_bytes).to_bytes(4, 'big')
        self.socket.sendall(length + data_bytes)
        
    def _recv_data(self):
        """Receive length-prefixed data"""
        length_bytes = self._recv_all(4)
        if not length_bytes:
            return None
        length = int.from_bytes(length_bytes, 'big')
        return self._recv_all(length).decode('utf-8')
        
    def _recv_all(self, n):
        """Receive exactly n bytes"""
        data = bytearray()
        while len(data) < n:
            packet = self.socket.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return bytes(data)


# Helper functions for quick messaging
def create_player_update(player_data):
    return {
        'type': MessageType.PLAYER_UPDATE.value,
        'data': player_data
    }

def create_block_place(x, y, block_type='platform'):
    return {
        'type': MessageType.BLOCK_PLACE.value,
        'data': {'x': x, 'y': y, 'type': block_type}
    }

def create_block_remove(x, y):
    return {
        'type': MessageType.BLOCK_REMOVE.value,
        'data': (x, y)
    }