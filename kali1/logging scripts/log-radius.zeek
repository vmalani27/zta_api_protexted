@load base/protocols/conn

module RADIUS;

event zeek_init() {
    Log::write(Zeek::INFO, "RADIUS logging enabled on UDP port 1812");
}

event udp_packet(c: connection, is_orig: bool, len: count, data: string) {
    if (c$id$resp_p == 1812/udp || c$id$orig_p == 1812/udp) {
        print fmt("📡 RADIUS packet: %s:%s -> %s:%s | Length: %d",
                  c$id$orig_h, c$id$orig_p,
                  c$id$resp_h, c$id$resp_p,
                  len);
    }
}

