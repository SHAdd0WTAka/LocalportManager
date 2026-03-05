# 🔒 LocalPortManager Secure Architecture

## Das Problem: Docker + VPN = MITM Risk

### Angriffsszenario

```
┌─────────────────────────────────────────────────────────────────┐
│                         ANGREIFER                                │
│                     (im gleichen Netz)                           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                         VPN TUNNEL                               │
│         (Traffic wird umgeleitet, Routing verändert)            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
    ┌──────────────────┴──────────────────┐
    │                                     │
    ▼                                     ▼
┌──────────┐                      ┌──────────────┐
│  Docker  │◀── 0.0.0.0:8080 ───▶ │  Container   │
│  Port    │    (öffentlich!)     │  App         │
└──────────┘                      └──────────────┘
```

**Wie der Angriff funktioniert:**
1. Docker bindet standardmäßig an `0.0.0.0` (alle Interfaces)
2. VPN manipuliert Routing-Tabellen
3. Ein Angreifer im gleichen Netzwerk kann den Docker Port erreichen
4. VPN verschlüsselt zwar den Traffic, aber Docker Port ist direkt erreichbar

## Die Lösung: Defense in Depth

### Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                    LocalPortManager Secure                       │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ VPN Detector │  │ Kill Switch  │  │ Secure Docker Mode   │  │
│  │              │  │              │  │                      │  │
│  │ • tun0/tun1  │  │ • Blockiert  │  │ • 127.0.0.1 binding  │  │
│  │ • wg0/wg1    │  │   Docker     │  │ • Isolated networks  │  │
│  │ • Prozesse   │  │   bei VPN    │  │ • No --network host  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                     │              │
│         └─────────────────┴─────────────────────┘              │
│                           │                                    │
│                           ▼                                    │
│              ┌────────────────────────┐                       │
│              │   Secure Proxy (1355)  │                       │
│              │   nur 127.0.0.1        │                       │
│              └───────────┬────────────┘                       │
└──────────────────────────┼────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  Service A │  │  Service B │  │  Docker C  │
    │  :4001     │  │  :4002     │  │  :4003     │
    └────────────┘  └────────────┘  └────────────┘
```

## Sicherheitsstufen

### 1. Standard (Kein VPN)
```bash
# Normale Registrierung - kein VPN aktiv
python localportmanager_secure.py register app "docker run -p {port}:80 nginx"

Result:
- Docker läuft normal
- Port auf 127.0.0.1 gebunden
- Keine Einschränkungen
```

### 2. Kill Switch (VPN aktiv)
```bash
# VPN ist aktiv - Kill Switch greift
python localportmanager_secure.py register app "docker run -p {port}:80 nginx"

Result:
⚠️  SECURITY BLOCK: Service 'app'
    Docker containers with exposed ports are BLOCKED when VPN is active.
    Reason: MITM attack risk through VPN tunnel manipulation.
```

### 3. Bypass (NICHT EMPFOHLEN)
```bash
# Nur für vertrauenswürdige Umgebungen
python localportmanager_secure.py register app "docker run -p {port}:80 nginx" --no-kill-switch
```

### 4. Isolated Network
```bash
# Maximum Security - isoliertes Netzwerk
python localportmanager_secure.py register db "docker run -p {port}:5432 postgres" --isolated

Result:
- Container in internem Netzwerk
- Kein Zugriff auf externe Netzwerke
- Nur über Proxy erreichbar
```

## Technische Details

### VPN Detection

```python
class VPNDectector:
    """Erkennt VPN-Verbindungen durch:"""
    
    # 1. Netzwerk-Interface Patterns
    VPN_PATTERNS = [
        r'tun\d+',      # OpenVPN
        r'wg\d+',       # WireGuard
        r'ppp\d+',      # PPTP
        r'proton',      # ProtonVPN
        r'nord',        # NordVPN
    ]
    
    # 2. Prozess-Detection
    VPN_PROCESSES = [
        'openvpn', 'wireguard', 'protonvpn',
        'nordvpn', 'mullvad-vpn'
    ]
    
    # 3. Routing-Table-Check
    # Überprüft auf Tunnel-Interfaces in Routing-Tabelle
```

### Secure Docker Command Transformation

```bash
# UNSICHER (Standard Docker)
docker run -p 8080:80 nginx
# Bindet an: 0.0.0.0:8080 (alle Interfaces!)

# SICHER (LocalPortManager Secure)
docker run -p 127.0.0.1:8080:80 nginx
# Bindet an: 127.0.0.1:8080 (nur localhost)
```

### Automatische Transformation

```python
def secure_docker_command(self, command: str) -> str:
    # Pattern: -p PORT:CONTAINER_PORT
    patterns = [
        (r'-p\s+(\d+):(\d+)', r'-p 127.0.0.1:\1:\2'),
    ]
    
    for pattern, replacement in patterns:
        command = re.sub(pattern, replacement, command)
    
    return command
```

## Deployment-Strategien

### Option A: Kein Docker + VPN gleichzeitig
```bash
# Wenn VPN aktiv, keine Docker-Ports exposen
# Stattdessen: Native Services verwenden
python localportmanager_secure.py register app "python -m http.server {port}"
```

### Option B: Separate Netzwerk-Namespaces
```bash
# Docker in isoliertem Namespace
sudo ip netns add docker-secure
sudo ip netns exec docker-secure dockerd

# LocalPortManager im Default Namespace
python localportmanager_secure.py proxy
```

### Option C: Reverse Proxy ohne Docker-Kontakt
```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Internet   │─────▶│   Reverse    │      │    Docker    │
│              │      │   Proxy      │ ╳    │   Container  │
└──────────────┘      │  (Nginx/     │──────┤   (isoliert) │
                      │   Traefik)   │      └──────────────┘
                      └──────────────┘      
                           │
                           ▼
                      ┌──────────────┐
                      │   Local      │
                      │   Services   │
                      └──────────────┘
```

## Best Practices

### 1. Immer 127.0.0.1 binding verwenden
```bash
# Gut
-p 127.0.0.1:8080:80

# Schlecht
-p 8080:80
```

### 2. Kein --network host
```bash
# Vermeiden
--network host

# Stattdessen
--network bridge
--network lpm-isolated
```

### 3. Firewall-Regeln
```bash
# Docker-Ports von außen blockieren
sudo iptables -A INPUT -p tcp --dport 4000:4999 -j DROP

# Nur localhost erlauben
sudo iptables -A INPUT -p tcp -s 127.0.0.1 --dport 4000:4999 -j ACCEPT
```

### 4. VPN Kill Switch auf System-Ebene
```bash
# Wenn VPN down, kein Internet
sudo iptables -A OUTPUT -o tun0 -j ACCEPT
sudo iptables -A OUTPUT -o lo -j ACCEPT
sudo iptables -A OUTPUT -j DROP
```

## Monitoring

### Security Status prüfen
```bash
python localportmanager_secure.py security

Output:
==================================================
🔒 SECURITY STATUS
==================================================
VPN Active:       YES ⚠️
Kill Switch:      ENABLED
Blocked Services: 2

VPN Interfaces:   tun0

Blocked Services:
  - grafana
  - prometheus
==================================================
```

### Logging
```
[2024-03-05 14:30:00] 🔒 GET /api/data HTTP/1.1
[2024-03-05 14:30:01] 🔒 POST /webhook HTTP/1.1
# 🔒 = VPN aktiv
```

## Integration mit Zen-AI-Pentest

```python
# In Zen-AI-Pentest verwenden
from localportmanager_secure import SecureLocalPortManager, VPNDectector

def start_secure_service(service_name: str, command: str):
    lpm = SecureLocalPortManager()
    
    # Prüft automatisch VPN-Status
    try:
        port = lpm.register_service(service_name, command)
        return f"http://{service_name}.localhost:1355"
    except RuntimeError as e:
        # VPN aktiv + Docker = blockiert
        logger.warning(f"Service blocked: {e}")
        # Fallback zu nativem Service
        return start_native_service(service_name)
```

## Zusammenfassung

| Feature | Standard LPM | LPM Secure |
|---------|-------------|------------|
| VPN Detection | ❌ | ✅ |
| Kill Switch | ❌ | ✅ |
| 127.0.0.1 Binding | ❌ | ✅ |
| Isolated Networks | ❌ | ✅ |
| MITM Protection | ❌ | ✅ |

**Empfehlung**: Immer `localportmanager_secure.py` verwenden wenn Docker + VPN im Spiel sind!
