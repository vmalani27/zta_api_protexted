FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install required packages
RUN apt-get update && apt-get install -y \
    nftables \
    freeradius \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /etc/nftables \
    /etc/freeradius/3.0

# Copy configuration files
COPY config/freeradius /etc/freeradius/3.0
COPY config/nftables /etc/nftables
COPY scripts/start.sh /start.sh
RUN chmod +x /start.sh

# Expose required ports
EXPOSE 1812/udp 1813/udp

# Set entrypoint
ENTRYPOINT ["/start.sh"] 