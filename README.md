# Auto Config LiteBeam M5 (Station)

![CLI Output](screenshot/output.png)
![LiteBeam M5](screenshot/litebeem.png)

A fully automated Python CLI tool designed to provision, configure, and manage Ubiquiti LiteBeam M5 airOS devices operating in Station mode.

This tool connects to brand-new or existing units via SSH, bypasses modern host-key restrictions to support legacy airOS `ssh-rsa` protocols, performs a live wireless site survey, and dynamically injects the optimal configuration directly into the device's flash memory.

## 🚀 Features

- Automated Site Survey (Smart AP Selection): runs `iwlist ath0 scan` internally on the device, parses detected networks, and selects the best available AP based on signal strength.
- Static IP Configuration: supports assigning and deploying static LAN IP settings to the LiteBeam.
- Legacy Protocol Support: wraps native OS SSH/SCP tools via `sshpass`, forces legacy SCP behavior, and explicitly uses `ssh-rsa` compatibility for old airOS firmware.
- PPPoE & Credential Injection: rewrites PPPoE credentials, device hostname, and WPA keys inside the raw `system.cfg` payload.
- Zero-Touch Flashing: uploads the updated config to `/tmp`, writes it to flash memory using `/sbin/cfgmtd`, and performs a safe soft-restart automatically.

## 📁 Project Structure

```text
airOS-AutoProvision/
├── config/
│   └── ap_list.json         # authorized access points and WPA keys
├── screenshot/
│   ├── litebeem.png         # hardware reference image
│   └── output.png           # CLI output screenshot
├── temp/                    # temporary payload storage
├── XW-B4FBE46CFAEF.cfg      # base airOS configuration template
├── main.py                  # CLI entry point
├── requirements.txt         # Python dependencies
├── README.md                # project documentation
```

## 🛠️ Prerequisites

This tool depends on `sshpass` for legacy SSH/SCP operations.

### Arch Linux

```bash
sudo pacman -S sshpass
```

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install sshpass
```

If you are using a virtual environment, create/activate it and install Python dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## ⚙️ Access Point Configuration

Create or edit `config/ap_list.json` with the SSIDs and passwords of the APs you want the LiteBeam to consider during the site survey.

Example:

```json
[
  {
    "ssid": "Your AP Name",
    "password": "your_wifi_password_here"
  },
  {
    "ssid": "Another AP Name",
    "password": "another_wifi_password_here"
  }
]
```

The script scans nearby wireless networks, filters the detected list against this file, and chooses the strongest matching AP.

## 💻 Usage

Example command:

```bash
python main.py \
  --device-ip 192.168.5.17 \
  --ssh-user ubnt \
  --ssh-pass ubnt123 \
  --pppoe-user "91188" \
  --pppoe-pass "91188" \
  --lan-ip "192.168.5.17" \
  --dev-name "LiteBeam MX"
```

For a brand-new Ubiquiti device, the default IP and credentials are typically:

- IP: `192.168.1.20`
- Username: `ubnt`
- Password: `ubnt`

### CLI Arguments

| Argument | Description | Default |
| --- | --- | --- |
| `--device-ip` | IP address of the LiteBeam to configure | `192.168.1.20` |
| `--ssh-user` | SSH username for the airOS device | `ubnt` |
| `--ssh-pass` | SSH password for the airOS device | `ubnt` |
| `--pppoe-user` | New PPPoE username to inject | Required |
| `--pppoe-pass` | New PPPoE password to inject | Required |
| `--lan-ip` | New static LAN IP to assign to the device | Required |
| `--dev-name` | New hostname for the device | Required |
| `--ap-list` | Path to the authorized AP list file | `config/ap_list.json` |
| `--config` | Path to the base configuration template | `XW-B4FBE46CFAEF.cfg` |

## 🔍 How It Works

1. Connects to the device using SSH and `sshpass` with compatibility settings for legacy airOS firmware.
2. Runs a wireless scan on `ath0` and parses the output to identify nearby access points.
3. Matches the discovered SSIDs against `config/ap_list.json`.
4. Selects the strongest AP and prepares a new configuration payload.
5. Rewrites the base `system.cfg` template with PPPoE, WPA, hostname, and LAN settings.
6. Uploads the payload to `/tmp` and commits it to flash using `/sbin/cfgmtd`.
7. Performs a soft restart to apply the configuration.

## ⚠️ Security and Safety Notes

- This tool modifies network and authentication settings on airOS devices.
- Use it only on equipment you own or are authorized to manage.
- Do not commit real Wi-Fi passwords, PPPoE credentials, or production device data to version control.
- Verify the device IP and SSH credentials before running any provisioning command.

## 📌 License

This project is provided for educational and authorized network administration use. Please use it responsibly and in compliance with local laws and your network policies.

## 🙌 Project Purpose

This repository was created to automate the setup and provisioning of Ubiquiti LiteBeam M5 devices that use legacy airOS firmware, reducing manual configuration effort while preserving compatibility with older device software.
