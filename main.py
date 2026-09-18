#!/usr/bin/env python3
import argparse
import json
import re
import sys
import os
import subprocess
from datetime import datetime

def log_msg(level, message):
    timestamp = datetime.now().strftime("%Y-%m-%d | %H:%M:%S")
    print(f"[{timestamp}][{level}] {message}")

def run_ssh_cmd(ip, user, password, cmd, timeout=30):
    ssh_cmd = [
        'sshpass', '-p', password,
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-o', 'HostKeyAlgorithms=+ssh-rsa',
        '-o', 'PubkeyAcceptedAlgorithms=+ssh-rsa',
        '-o', 'LogLevel=ERROR',
        f'{user}@{ip}',
        cmd
    ]
    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        log_msg("ERROR", "The 'sshpass' utility is not installed. Run: pkg install sshpass openssh")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        log_msg("ERROR", f"Command timed out after {timeout} seconds: {cmd}")
        sys.exit(1)

def upload_file(ip, user, password, local_path, remote_path, timeout=30):
    scp_cmd = [
        'sshpass', '-p', password,
        'scp',
        '-O',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-o', 'HostKeyAlgorithms=+ssh-rsa',
        '-o', 'PubkeyAcceptedAlgorithms=+ssh-rsa',
        '-o', 'LogLevel=ERROR',
        local_path,
        f'{user}@{ip}:{remote_path}'
    ]
    try:
        result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        log_msg("ERROR", "The 'sshpass' utility is not installed. Run: pkg install sshpass openssh")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        log_msg("ERROR", "SCP file upload timed out.")
        sys.exit(1)

def load_ap_list(json_path):
    log_msg("INFO", f"Loading available AP credentials from {json_path}...")
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        log_msg("ERROR", f"Failed to load {json_path}: {e}")
        sys.exit(1)

def scan_and_find_best_ap(ip, user, password, ap_list):
    log_msg("INFO", "Initiating wireless site survey on ath0 interface...")
    
    code, stdout, stderr = run_ssh_cmd(ip, user, password, 'iwlist ath0 scan')
    
    if code != 0:
        log_msg("ERROR", f"Failed to execute iwlist scan: {stderr.strip()}")
        sys.exit(1)
        
    if stderr:
        log_msg("WARNING", f"Scan standard error output: {stderr.strip()}")
    
    log_msg("INFO", "Parsing scanning results...")
    scanned_networks = []
    
    cells = stdout.split('Cell ')
    for cell in cells[1:]:
        ssid_match = re.search(r'ESSID:"([^"]+)"', cell)
        signal_match = re.search(r'Signal level=(-\d+) dBm', cell)
        
        if ssid_match and signal_match:
            ssid = ssid_match.group(1)
            signal = int(signal_match.group(1))
            scanned_networks.append({'ssid': ssid, 'signal': signal})
            log_msg("INFO", f"Detected network in range: '{ssid}' with signal {signal} dBm")
            
    if not scanned_networks:
        log_msg("ERROR", "No wireless networks detected during the scan.")
        sys.exit(1)
        
    log_msg("INFO", "Cross-referencing scanned networks with authorized AP list...")
    best_ap = None
    best_signal = -9999 
    
    for scanned in scanned_networks:
        for known_ap in ap_list:
            if known_ap['ssid'] == scanned['ssid']:
                if scanned['signal'] > best_signal:
                    best_signal = scanned['signal']
                    best_ap = {
                        'ssid': known_ap['ssid'],
                        'password': known_ap['password'],
                        'signal': scanned['signal']
                    }
                    
    if best_ap:
        log_msg("SUCCESS", f"Best AP Selected: '{best_ap['ssid']}' (Strongest Signal: {best_ap['signal']} dBm)")
        return best_ap
    else:
        log_msg("ERROR", "No matching access points from your JSON file were found in the vicinity.")
        sys.exit(1)

def modify_config(input_file, output_file, pppoe_user, pppoe_pass, lan_ip, dev_name, ap_ssid, ap_pass, dhcp_start, dhcp_end, dhcp_netmask):
    log_msg("INFO", f"Modifying base configuration file template: {input_file}")
    
    try:
        with open(input_file, 'r') as f:
            config_data = f.read()
    except FileNotFoundError:
        log_msg("ERROR", f"The base configuration file {input_file} could not be located in your current folder.")
        sys.exit(1)

    config_data = re.sub(r'ppp\.1\.name=.*', f'ppp.1.name={pppoe_user}', config_data)
    config_data = re.sub(r'ppp\.1\.password=.*', f'ppp.1.password={pppoe_pass}', config_data)
    config_data = re.sub(r'netconf\.2\.ip=.*', f'netconf.2.ip={lan_ip}', config_data)
    config_data = re.sub(r'resolv\.host\.1\.name=.*', f'resolv.host.1.name={dev_name}', config_data)
    config_data = re.sub(r'wireless\.1\.ssid=.*', f'wireless.1.ssid={ap_ssid}', config_data)
    config_data = re.sub(r'wpasupplicant\.profile\.1\.network\.1\.ssid=.*', f'wpasupplicant.profile.1.network.1.ssid={ap_ssid}', config_data)
    config_data = re.sub(r'aaa\.1\.wpa\.psk=.*', f'aaa.1.wpa.psk={ap_pass}', config_data)
    config_data = re.sub(r'wpasupplicant\.profile\.1\.network\.1\.psk=.*', f'wpasupplicant.profile.1.network.1.psk={ap_pass}', config_data)
    
    config_data = re.sub(r'dhcpd\.1\.start=.*', f'dhcpd.1.start={dhcp_start}', config_data)
    config_data = re.sub(r'dhcpd\.1\.end=.*', f'dhcpd.1.end={dhcp_end}', config_data)
    config_data = re.sub(r'dhcpd\.1\.netmask=.*', f'dhcpd.1.netmask={dhcp_netmask}', config_data)
    config_data = re.sub(r'netconf\.2\.netmask=.*', f'netconf.2.netmask={dhcp_netmask}', config_data)

    try:
        with open(output_file, 'w') as f:
            f.write(config_data)
        log_msg("SUCCESS", f"Configuration customized successfully. Saved locally to {output_file}")
    except Exception as e:
        log_msg("ERROR", f"Failed to save temporary configuration to {output_file}: {e}")
        sys.exit(1)

def upload_and_apply(ip, user, password, local_cfg_path):
    log_msg("INFO", "Deploying configuration file via SCP...")
    remote_path = '/tmp/system.cfg'  # The LiteBeam's OS does use /tmp natively
    
    code, stdout, stderr = upload_file(ip, user, password, local_cfg_path, remote_path)
    if code != 0:
        log_msg("ERROR", f"SCP Upload failed: {stderr.strip()}")
        sys.exit(1)
        
    log_msg("SUCCESS", f"Uploaded temporary config to {remote_path} on target hardware.")

    log_msg("INFO", "Applying configuration to flash memory and initiating reboot. Device logs:")
    apply_command = '/sbin/cfgmtd -f /tmp/system.cfg -w && /usr/etc/rc.d/rc.softrestart save'
    
    code, stdout, stderr = run_ssh_cmd(ip, user, password, apply_command, timeout=60)
    
    if stdout:
        for line in stdout.strip().split('\n'):
            log_msg("DEVICE-STDOUT", line)
    
    if code == 0 or code == 255: 
        log_msg("SUCCESS", "Configuration committed successfully.")
    else:
        log_msg("ERROR", f"Flash write failure. Exit code: {code}. Error: {stderr.strip()}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Automate Brand New Ubiquiti LiteBeam M5 Setup (Termux Edition)")
    
    parser.add_argument('--device-ip', default="192.168.1.20", help="IP address (Defaults to 192.168.1.20)")
    parser.add_argument('--ssh-user', default="ubnt", help="SSH Username (Defaults to ubnt)")
    parser.add_argument('--ssh-pass', default="ubnt", help="SSH Password (Defaults to ubnt)")
    
    parser.add_argument('--pppoe-user', required=True, help="Your designated PPPoE Username")
    parser.add_argument('--pppoe-pass', required=True, help="Your designated PPPoE Password")
    parser.add_argument('--lan-ip', required=True, help="The new local LAN IP (e.g., 192.168.5.17)")
    parser.add_argument('--dev-name', required=True, help="The intended Device Hostname")
    
    parser.add_argument('--ap-list', default="config/ap_list.json", help="Path to your AP authorization list")
    parser.add_argument('--config', default="XW-B4FBE46CFAEF.cfg", help="The raw base configuration file to inject")
    
    args = parser.parse_args()
    
    ip_parts = args.lan_ip.split('.')
    if len(ip_parts) != 4:
        log_msg("ERROR", f"Invalid LAN IP format: {args.lan_ip}. Expected format: X.X.X.X")
        sys.exit(1)
        
    base_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
    dhcp_start = f"{base_ip}.{int(ip_parts[3]) + 1}"
    dhcp_end = f"{base_ip}.254"
    dhcp_netmask = "255.255.255.0"

    dev_ip_parts = args.device_ip.split('.')
    suggested_phone_ip = f"{dev_ip_parts[0]}.{dev_ip_parts[1]}.{dev_ip_parts[2]}.250"
    
    print("\n" + "="*60)
    print(" 🛑 MANUAL ANDROID NETWORK CONFIGURATION REQUIRED 🛑")
    print("="*60)
    print(f"To connect to the LiteBeam, your phone needs a static IP.")
    print(f"1. Go to your Android Wi-Fi or Ethernet settings.")
    print(f"2. Set your IP settings to 'Static'.")
    print(f"3. Enter IP Address: {suggested_phone_ip}")
    print(f"4. Return to Termux when connected.")
    print("="*60)
    input("\n👉 Press ENTER when your phone is connected with the Static IP...")
    print("\n")

    log_msg("INFO", f"Starting automated setup sequence for target IP {args.device_ip}...")
    log_msg("INFO", f"Calculated DHCP Range: {dhcp_start} - {dhcp_end} (Subnet: {dhcp_netmask})")
    
    log_msg("INFO", f"Attempting SSH login as '{args.ssh_user}'...")
    code, stdout, stderr = run_ssh_cmd(args.device_ip, args.ssh_user, args.ssh_pass, "echo 'auth_success'")
    if code != 0:
        log_msg("ERROR", f"Unreachable or invalid credentials: {stderr.strip()}")
        sys.exit(1)
        
    log_msg("SUCCESS", "SSH connection verified and established.")

    known_aps = load_ap_list(args.ap_list)
    best_ap = scan_and_find_best_ap(args.device_ip, args.ssh_user, args.ssh_pass, known_aps)
    
    # Write to current working directory to bypass Android /tmp limitations
    temp_config_output = "modified_XW_payload.cfg" 
    modify_config(
        input_file=args.config,
        output_file=temp_config_output,
        pppoe_user=args.pppoe_user,
        pppoe_pass=args.pppoe_pass,
        lan_ip=args.lan_ip,
        dev_name=args.dev_name,
        ap_ssid=best_ap['ssid'],
        ap_pass=best_ap['password'],
        dhcp_start=dhcp_start,
        dhcp_end=dhcp_end,
        dhcp_netmask=dhcp_netmask
    )
    
    upload_and_apply(args.device_ip, args.ssh_user, args.ssh_pass, temp_config_output)
    
    if os.path.exists(temp_config_output):
        os.remove(temp_config_output)
        log_msg("INFO", f"Temporary payload {temp_config_output} safely purged from local machine.")
        
    log_msg("SUCCESS", "Workflow complete. The LiteBeam M5 is currently rebooting.")
    
    print("\n" + "="*60)
    print(" ✅ SETUP COMPLETE ✅")
    print("="*60)
    print(f"The device will now broadcast its new network.")
    print(f"1. Go back to your Android Wi-Fi settings.")
    print(f"2. Change your IP settings back to 'DHCP'.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()