#!/bin/bash
# Basic usage examples for LocalPortManager

echo "=== LocalPortManager Basic Usage Examples ==="
echo

# Start proxy in background
echo "1. Starting proxy server..."
python ../localportmanager.py proxy &
PROXY_PID=$!
sleep 2

echo
echo "2. Registering services..."

# Register a simple HTTP server
python ../localportmanager.py register webapp "python -m http.server {port}" --yes

# Register another service
python ../localportmanager.py register api "python -m http.server {port}" --yes

echo
echo "3. Listing registered services..."
python ../localportmanager.py list

echo
echo "4. Checking proxy status..."
python ../localportmanager.py status

echo
echo "5. Test with curl:"
echo "   curl http://webapp.localhost:1355"
echo "   curl http://api.localhost:1355"

echo
echo "6. Cleanup - stop proxy (kill $PROXY_PID)"
echo "   kill $PROXY_PID"

echo
echo "Done!"
