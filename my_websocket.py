import socket
import hashlib
import base64
from enum import Enum
import json
import base64
# from message_types import MessageTypes
import ssl

#region ---> Handles the WebSocket handshake

def recv_http_handshake_msg(soc:socket.socket) ->bytes:
    data=b""
    while b'\r\n\r\n' not in data:
        chunk=soc.recv(1024)
        if not chunk:
            return data
        data+=chunk
    return data



class HttpMessage:
    def __init__(self, http_method, protcol_version, host, upgrade,connection, websocket_key):
        self.http_method = http_method
        self.protocol_version = protcol_version
        self.host = host
        self.upgrade = upgrade
        self.connection = connection
        self.websocket_key = websocket_key

    def __repr__(self):
        return(        
        f"Http method        : {self.http_method}\n"
        f"Protocol version   : {self.protocol_version}\n"
        f"Server             : {self.host}\n"
        f"Upgrade to         : {self.upgrade}\n"
        f"Connection type    : {self.connection}\n"
        f"WebSocket key      : {self.websocket_key}"
        )



class HttpMessageParser:
    
    @staticmethod
    def parse_http_message(msg: bytes) -> HttpMessage:
        headers = msg.split(b'\r\n\r\n')[0].decode()
        lines = headers.split('\r\n')
        http_method, _, protocol_version = lines[0].split(' ')

        header_dict = {}
        for line in lines[1:]:
            key, value = line.split(": ", 1)
            header_dict[key] = value
        try:
            return HttpMessage(
                http_method,
                protocol_version,
                host=header_dict["Host"],
                upgrade=header_dict["Upgrade"],
                connection=header_dict["Connection"],
                websocket_key=header_dict["Sec-WebSocket-Key"],
            )
        except Exception as e:
            print(f"Found exception ---- {e}")
            return None


#Build the Http Upgrade message
class HttpUpgrade:

    def __init__(self, http_message:HttpMessage):
        self.message = http_message

    def to_upgrade_to_WebSocket(self) -> bool:
        if self.message.connection != "Upgrade":
            return False
        elif self.message.upgrade != "websocket":
            return False
        else:
            return True
        
    def upgrade_response(self) -> str:
        GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        contecation:str = self.message.websocket_key.strip()+GUID
        sha1_hash = hashlib.sha1(contecation.encode()).digest()    
        accept_text = base64.b64encode(sha1_hash).decode("ASCII")
        
        version = "HTTP/1.1 "
        accept_code = "101 Switching Protocols\r\n"
        upgrade = f"Upgrade: {self.message.upgrade}\r\n"
        connection = f"Connection: {self.message.connection}\r\n"
        accept_key = f"Sec-WebSocket-Accept: {accept_text}\r\n"
        return_text = f"{version}{accept_code}{upgrade}{connection}{accept_key}\r\n"
        return return_text

#endregion 




class WebSocketOpcodes(Enum):
    CONTINUATION = 0x0
    TEXT = 0x1
    BINARY = 0x2
    CLOSE_CONNECTION = 0x8
    PING_MESSAGE = 0x9
    PONG_MESSAGE = 0xA
    

#Builds WebSocket messages
class WebSocketMessageFactory:
    def __init__(self, opcode:WebSocketOpcodes, to_split=None, payload=None): #All types of message except for pong
        self.opcode:WebSocketOpcodes = opcode
        self.to_split = to_split
        self.payload = payload
        if self.payload ==None:
            self.payload =''
            
        if self.opcode != WebSocketOpcodes.PONG_MESSAGE and to_split==None:
            raise RuntimeError("Expected to recieve 'to_split' value but none was given")
        else:
            self.message_to_send = self._build_pong_message() if self.opcode == WebSocketOpcodes.PONG_MESSAGE else self._build_websocket_message()
    
     
    def __repr__(self):
        to_print = f"Message content type - {self.opcode}"
        if self.to_split != None:
            to_print+=f"\nMessage needs to be splited - {'True' if self.to_split else 'False'}"
        if self.payload:
            to_print+=f"\nMessage content - {self.payload}"
        
        to_print+=f"\nMessage to be sent - {self.message_to_send}"
        return to_print
    
    
    def _build_websocket_message(self) ->bytes:
        frame_bytes = bytearray()
    
        fin = 0 if self.to_split else 1
        frame_bytes.append((fin<<7)|self.opcode.value)
        
        mask = 0 
        bytes_payload = self.payload if type(self.payload)==bytes else self.payload.encode("UTF-8")
        
        def get_length_bits(bytes_payload):
            payload_length = len(bytes_payload)
            
            if payload_length<=125:
                length_field = payload_length
                extended_length_bytes = b''
            
            elif payload_length<=65535:
                length_field = 126
                extended_length_bytes = payload_length.to_bytes(2, "big")
            
            else:
                length_field = 127
                extended_length_bytes = payload_length.to_bytes(8, "big")
            
            return length_field, extended_length_bytes
        
        length_field, extend_length_bytes = get_length_bits(bytes_payload)
        frame_bytes.append((mask<<7)|length_field)
        frame_bytes.extend(extend_length_bytes)
        frame_bytes.extend(bytes_payload)
        return (bytes(frame_bytes))

    
    def _build_pong_message(self):
        frame_bytes = bytearray()
        fin = 1
        frame_bytes.append((fin<<7)|WebSocketOpcodes.PONG_MESSAGE.value)
        
        
        mask = 0 
        if self.payload:
            bytes_payload = self.payload if type(self.payload)==bytes else self.payload.encode("UTF-8")
            payload_length = len(bytes_payload)
            frame_bytes.append((mask<<7)|payload_length)
            frame_bytes.extend(bytes_payload)
        else:
            payload_length = 0
            frame_bytes.append((mask<<7)|payload_length)
            
        return(bytes(frame_bytes))



#region ---> WebSocket message parser

   
class WebSocketFrame:
    def __init__(self, fin, opcode, masked, payload_length, payload, masking_key=None):
        self.message_is_split = False if fin == 1 else True
        self.opcode = WebSocketOpcodes(opcode)
        self.masked = bool(masked)
        self.payload_length = payload_length
        self.payload = payload       
        if masking_key:
            self.masking_key = masking_key
    
    def __repr__(self):
        to_print = ""
        if self.message_is_split:
            to_print+="Message is splitted"
        else:
            to_print+="This is the whole message"
        to_print+=f"\nMessage type :{self.opcode}"
        to_print+=f"\nthis message is {'masked' if self.masked else 'not masked'}"
        to_print+=f"\nThe payload length is :{self.payload_length}"
        to_print+=f"\nPayload :{self.payload}"
        if self.masking_key:
            to_print+=f"\nMasking key :{self.masking_key}"
        return to_print
         
  
   
class WebSocketMessageParser:
    @staticmethod
    def _parse_one_frame(clt:socket.socket) ->WebSocketFrame:
        first_byte = clt.recv(1)[0]
        fin = (first_byte>>7) & 1
        opcode = first_byte & 0x0F
        
        second_byte = clt.recv(1)[0]
        masked = (second_byte>>7) & 1
        
        payload_len = second_byte & 0x7F
        if payload_len == 126:
            bytes_of_extended = clt.recv(2)
            payload_len = int.from_bytes(bytes_of_extended, "big")
        elif payload_len == 127:
            bytes_of_extended = clt.recv(8)
            payload_len = int.from_bytes(bytes_of_extended, "big")
            
        if masked:
            mask = clt.recv(4)
        else:
            mask= None
            
        payload = b""
        bytes_to_read = payload_len
        while bytes_to_read>0:
            chunk = clt.recv(bytes_to_read)
            if not chunk:
                raise RuntimeError("Connection closed by the client")
            payload+=chunk
            bytes_to_read-=len(chunk)
        
        if masked:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        
        return WebSocketFrame(fin, opcode, masked, payload_len, payload, masking_key=mask)
    
    @staticmethod
    def parse_message(clt:socket.socket) ->bytes:
        buffer = b''

        while True:
            frame = WebSocketMessageParser._parse_one_frame(clt)
            
            if frame.opcode in {WebSocketOpcodes.CLOSE_CONNECTION,
                                WebSocketOpcodes.PING_MESSAGE,
                                WebSocketOpcodes.PONG_MESSAGE}: 
                if frame.payload_length>=125 or frame.message_is_split:
                    return b'FAULTY FRAME'
                if frame.opcode ==WebSocketOpcodes.CLOSE_CONNECTION:
                    clt.close()
                    return b"CLIENT CLOSED"
                elif frame.opcode==WebSocketOpcodes.PING_MESSAGE:    
                    to_send = WebSocketMessageFactory(WebSocketOpcodes.PONG_MESSAGE, payload=frame.payload)
                    clt.send(to_send.message_to_send)
                continue
                
            if frame.opcode not in {WebSocketOpcodes.CONTINUATION,
                                    WebSocketOpcodes.TEXT,
                                    WebSocketOpcodes.BINARY} or (frame.opcode == WebSocketOpcodes.CONTINUATION and buffer == b''):
                return b"FAULTY FRAME"
            
            buffer+=frame.payload
                
            if not frame.message_is_split:
                break
            
        return buffer

#endregion
        
        
#region accept client
def accept_client(clt_soc):
    new_soc = accept_TLS_encryption(clt_soc)
    accept_websocket_upgrade_request_from_client(new_soc)
    return new_soc

    
def accept_TLS_encryption(clt_soc):
    CERTIFICATE_PATH = r"C:\Coding\pro-find\certificate\server.crt"
    KEY_PATH = r"C:\Coding\pro-find\certificate\server.key"
    # CERTIFICATE_PATH =r"D:\pro-find\certificate\server.crt"
    # KEY_PATH = r"D:\pro-find\certificate\server.key"
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.verify_mode = ssl.CERT_NONE
    context.load_cert_chain(certfile=CERTIFICATE_PATH, keyfile=KEY_PATH)
    tls_soc = context.wrap_socket(clt_soc, server_side=True)
    return tls_soc


def accept_websocket_upgrade_request_from_client(clt_soc:socket.socket):
    info = recv_http_handshake_msg(clt_soc)
    http_message = HttpMessageParser.parse_http_message(info)
    
    accept_WebSocket_upgrade = HttpUpgrade(http_message)
    if accept_WebSocket_upgrade.to_upgrade_to_WebSocket():
        to_send = accept_WebSocket_upgrade.upgrade_response()
        clt_soc.send(to_send.encode())
        print("Connected")
#endregion
        
        
        
        
def build_proper_json_payload(type, payload, token):
    type_of_message = type.value
    type_of_data = "JSON"

    if isinstance(payload, bytes):
        safe_payload = base64.b64encode(payload).decode("utf-8")
        type_of_data = "BYTES"
    else:
        try:
            json.dumps(payload) 
            safe_payload = payload
        except (TypeError, OverflowError):
            safe_payload = str(payload)

    return {
        "type": type_of_message,
        "data": safe_payload,
        "data_type": type_of_data,
        "token":token
    }


def send_message(clt: socket.socket, type, token, msg=None, to_split_message=None, opcode:WebSocketOpcodes=WebSocketOpcodes.TEXT):
    try:
        msg_dict = build_proper_json_payload(type, msg, token) if msg is not None else None
        
        msg_to_send = json.dumps(msg_dict)
        
        message = WebSocketMessageFactory(opcode, to_split=to_split_message, payload=msg_to_send)
        clt.send(message.message_to_send)
        return True

    except Exception as e:
        print("Failed to send message:", e)
        return False





def recv_message(clt:socket.socket):
    try:
        parsed_message = WebSocketMessageParser.parse_message(clt)
        if parsed_message == b'FAULTY FRAME' or parsed_message == b"CLIENT CLOSED":
            return None
        else:
            return json.loads(parsed_message)
    except Exception as e:
        print(e)
        return None
    
    

