#!/usr/bin/env python3
import socket
import threading
import time
import logging
import os
from dotenv import load_dotenv
import json
from typing import Dict, List, Set
import ipaddress

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PortKnockServer:
    def __init__(self):
        # Port knocking configuration
        self.knock_sequence = [int(p) for p in os.getenv("KNOCK_SEQUENCE", "7000,8000,9000").split(",")]
        self.knock_timeout = int(os.getenv("KNOCK_TIMEOUT", "10"))  # seconds
        self.port_open_duration = int(os.getenv("PORT_OPEN_DURATION", "30"))  # seconds
        
        # Service ports to protect
        self.protected_ports = [int(p) for p in os.getenv("PROTECTED_PORTS", "5001,5002,5003").split(",")]
        
        # State tracking
        self.active_knocks: Dict[str, List[int]] = {}  # IP -> [ports knocked]
        self.open_ports: Dict[str, Set[int]] = {}  # IP -> set of open ports
        self.knock_timestamps: Dict[str, float] = {}  # IP -> last knock time
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_knocks, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"Port knock server initialized with sequence: {self.knock_sequence}")
        logger.info(f"Protecting ports: {self.protected_ports}")

    def _monitor_knocks(self):
        """Monitor and clean up expired knocks and open ports"""
        while True:
            current_time = time.time()
            # Clean up expired knocks
            expired_knocks = [
                ip for ip, timestamp in self.knock_timestamps.items()
                if current_time - timestamp > self.knock_timeout
            ]
            for ip in expired_knocks:
                del self.active_knocks[ip]
                del self.knock_timestamps[ip]
            
            # Clean up expired open ports
            expired_ports = [
                ip for ip, ports in self.open_ports.items()
                if current_time - self.knock_timestamps.get(ip, 0) > self.port_open_duration
            ]
            for ip in expired_ports:
                del self.open_ports[ip]
            
            time.sleep(1)

    def handle_knock(self, client_ip: str, port: int) -> bool:
        """Handle a port knock attempt"""
        current_time = time.time()
        
        # Initialize or reset sequence if timeout
        if client_ip not in self.active_knocks or \
           current_time - self.knock_timestamps[client_ip] > self.knock_timeout:
            self.active_knocks[client_ip] = []
            self.knock_timestamps[client_ip] = current_time
        
        # Update timestamp
        self.knock_timestamps[client_ip] = current_time
        
        # Check if port is in sequence
        expected_port = self.knock_sequence[len(self.active_knocks[client_ip])]
        if port != expected_port:
            logger.warning(f"Invalid knock sequence from {client_ip}: got {port}, expected {expected_port}")
            self.active_knocks[client_ip] = []
            return False
        
        # Add to sequence
        self.active_knocks[client_ip].append(port)
        
        # Check if sequence is complete
        if len(self.active_knocks[client_ip]) == len(self.knock_sequence):
            logger.info(f"Valid knock sequence from {client_ip}")
            self.open_ports[client_ip] = set(self.protected_ports)
            self.active_knocks[client_ip] = []
            return True
        
        return False

    def is_port_open(self, client_ip: str, port: int) -> bool:
        """Check if a port is open for a client"""
        return port in self.open_ports.get(client_ip, set())

    def start_server(self):
        """Start the port knock server"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to all interfaces
        server.bind(('0.0.0.0', 0))
        server.listen(5)
        
        logger.info(f"Port knock server listening on {server.getsockname()}")
        
        while True:
            try:
                client, addr = server.accept()
                client_ip = addr[0]
                client_port = addr[1]
                
                # Handle the knock
                if self.handle_knock(client_ip, client_port):
                    logger.info(f"Ports opened for {client_ip}: {self.open_ports[client_ip]}")
                
                client.close()
                
            except Exception as e:
                logger.error(f"Error handling connection: {e}")

def main():
    server = PortKnockServer()
    server.start_server()

if __name__ == "__main__":
    main() 