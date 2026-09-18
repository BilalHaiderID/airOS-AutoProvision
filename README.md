# airOS AutoProvision

<p align="center">
  <img src="screenshot/litebeem.png" alt="Ubiquiti LiteBeam M5" width="420">
</p>

<p align="center"><strong>Automated provisioning for Ubiquiti LiteBeam M5 devices running legacy airOS.</strong></p>

<p align="center">
  <a href="https://github.com/BilalHaiderID/airOS-AutoProvision/blob/main/LICENSE">License</a> ·
  <a href="https://github.com/BilalHaiderID/airOS-AutoProvision/issues">Issues</a>
</p>

`airOS AutoProvision` is a lightweight Python command-line utility for authorized network administrators who need to provision Ubiquiti LiteBeam M5 devices in Station mode. It combines legacy SSH/SCP compatibility, wireless site surveying, configuration templating, PPPoE setup, LAN/DHCP configuration, and flash deployment into one guided workflow.

> **Important:** This project changes network access, wireless credentials, PPPoE settings, and device configuration. Use it only on equipment and networks that you own or are explicitly authorized to manage.

## Overview

The tool is designed for airOS firmware that requires older SSH algorithms and traditional SCP behavior. It uses the operating system's native `ssh`, `scp`, and `sshpass` commands rather than a third-party Python SSH library.

It can be run from a normal Linux workstation or from Termux on a non-rooted Android phone. The Termux workflow pauses while you temporarily assign a static IP to the phone through Android Wi-Fi settings.

![CLI output](screenshot/output.png)

## Features

- **Guided Termux workflow** for non-rooted Android devices.
- **Legacy airOS SSH compatibility** using `ssh-rsa` options and disabled host-key prompts for first-time device access.
- **Automated wireless survey** using `iwlist ath0 scan` on the LiteBeam.
- **Authorized AP matching** from a local JSON file, with strongest-signal selection.
- **Configuration templating** for PPPoE credentials, hostname, wireless SSID/password, LAN address, netmask, and DHCP range.
- **Flash deployment** through `/sbin/cfgmtd` followed by an airOS soft restart.
- **Temporary payload cleanup** after the provisioning workflow completes.
- **No Python packages required** — the script uses only Python's standard library and system utilities.

## Requirements

### Hardware and firmware

- Ubiquiti LiteBeam M5 or compatible airOS device.
- SSH access to the device.
- A base airOS configuration template compatible with the target firmware.
- An authorized wireless network within range of the device.

### Host software

- Python 3.8 or newer.
- `sshpass`.
- OpenSSH client (`ssh` and `scp`).
- A network connection to the device.

Install the required system tools as follows.

#### Termux

```bash
pkg update
pkg install python openssh sshpass
```

#### Debian or Ubuntu

```bash
sudo apt update
sudo apt install python3 openssh-client sshpass
```

#### Arch Linux

```bash
sudo pacman -S python openssh sshpass
```

No `pip install` step is required.

## Installation

Clone the repository and enter its directory:

```bash
git clone https://github.com/BilalHaiderID/airOS-AutoProvision.git
cd airOS-AutoProvision
```

Verify the command-line interface:

```bash
python3 main.py --help
```

## Configuration

### Authorized AP list

Create or edit `config/ap_list.json`. Only networks listed in this file can be selected during the site survey.

```json
[
  {
    "ssid": "Your authorized AP",
    "password": "your_wifi_password"
  },
  {
    "ssid": "Backup authorized AP",
    "password": "another_wifi_password"
  }
]
```

The matching is based on the exact SSID. If more than one authorized AP is detected, the script selects the one with the strongest signal.

### Configuration template

`XW-B4FBE46CFAEF.cfg` is used as the base template. The script updates matching airOS keys for:

- PPPoE username and password
- Device hostname
- Station SSID and WPA credentials
- LAN IP address and netmask
- DHCP start and end addresses

Keep a backup of any production configuration before applying changes.

## Usage

For a factory-reset device, the commonly used default values are:

| Setting | Typical default |
| --- | --- |
| Device IP | `192.168.1.20` |
| SSH username | `ubnt` |
| SSH password | `ubnt` |

Run the tool with your authorized credentials and deployment values:

```bash
python3 main.py \
  --device-ip 192.168.1.20 \
  --ssh-user ubnt \
  --ssh-pass ubnt \
  --pppoe-user "your_pppoe_username" \
  --pppoe-pass "your_pppoe_password" \
  --lan-ip 192.168.5.17 \
  --dev-name "LiteBeam M5" \
  --ap-list config/ap_list.json \
  --config XW-B4FBE46CFAEF.cfg
```

> Do not copy real passwords into shell history or commit them to the repository. Replace all example values before running the command.

## Termux workflow

On a non-rooted Android phone, the script cannot change the Wi-Fi interface address itself.

1. Start the command from Termux.
2. When prompted, open Android Wi-Fi settings.
3. Change the connected network's IP setting to **Static**.
4. Enter the temporary IP shown by the script, typically an unused address in the device's current subnet.
5. Return to Termux and press **Enter**.
6. Allow the script to complete the survey, configuration, flash write, and restart.
7. Change the phone's Wi-Fi setting back to **DHCP**.

The device will normally become available at the new value supplied to `--lan-ip` after reboot.

## Command-line reference

| Option | Required | Default | Description |
| --- | :---: | --- | --- |
| `--device-ip` | No | `192.168.1.20` | Current IP address of the device. |
| `--ssh-user` | No | `ubnt` | Current SSH username. |
| `--ssh-pass` | No | `ubnt` | Current SSH password. |
| `--pppoe-user` | Yes | — | PPPoE username to write to the configuration. |
| `--pppoe-pass` | Yes | — | PPPoE password to write to the configuration. |
| `--lan-ip` | Yes | — | New device LAN IP address. |
| `--dev-name` | Yes | — | New device hostname. |
| `--ap-list` | No | `config/ap_list.json` | Authorized AP JSON file. |
| `--config` | No | `XW-B4FBE46CFAEF.cfg` | Base configuration template. |

The implementation's current argument list is always available with:

```bash
python3 main.py --help
```

## Provisioning flow

1. Calculates the target subnet and DHCP range.
2. Displays the temporary Android network instructions.
3. Verifies SSH connectivity.
4. Loads the authorized AP list.
5. Runs `iwlist ath0 scan` on the LiteBeam.
6. Selects the strongest matching authorized AP.
7. Generates a temporary customized configuration.
8. Uploads it to `/tmp/system.cfg` using legacy SCP mode.
9. Commits the configuration with `/sbin/cfgmtd`.
10. Performs a soft restart and removes the local temporary payload.

## Troubleshooting

### `sshpass` is not installed

Install `sshpass` using the platform-specific command in the Requirements section, then confirm it is available:

```bash
sshpass -V
```

### SSH connection fails

- Confirm the device is powered and connected to the same network.
- Verify the temporary static IP on Android or the host interface.
- Check `--device-ip`, `--ssh-user`, and `--ssh-pass`.
- Confirm that SSH is enabled on the device.

### No authorized AP is found

- Confirm the SSID is spelled exactly as it appears in the scan.
- Check that the AP is in range.
- Verify `config/ap_list.json` contains valid JSON and the correct password.
- Make sure the device's wireless interface is `ath0` on the installed firmware.

### The device is unreachable after reboot

Wait for the restart to finish, then connect using the new `--lan-ip`. If necessary, restore the previous configuration or perform a manufacturer-supported recovery procedure.

## Security guidance

- Treat `config/ap_list.json` and configuration templates as sensitive when they contain real credentials.
- Prefer a local, untracked credentials file for production deployments.
- Avoid passing secrets directly on the command line when shell history is shared.
- Do not disable network security controls on systems you do not administer.
- Review the generated configuration before flashing a production device.

## Project structure

```text
airOS-AutoProvision/
├── config/
│   └── ap_list.json         # Authorized AP definitions
├── screenshot/
│   ├── litebeem.png         # Hardware reference image
│   └── output.png           # Example CLI output
├── LICENSE                  # License terms
├── README.md                # Documentation
├── XW-B4FBE46CFAEF.cfg      # Base airOS configuration template
└── main.py                  # Provisioning CLI
```

## Contributing

Bug reports, documentation improvements, and compatibility fixes are welcome. When opening an issue, include:

- Host operating system and Python version
- airOS/device model and firmware version
- The command options used, with credentials removed
- Relevant error output and reproduction steps

Never include passwords, private keys, or production network details in issues or pull requests.

## License

See [LICENSE](LICENSE) for the license applicable to this project.

## Disclaimer

This project is provided as-is for authorized administration and educational purposes. The maintainers are not responsible for device outages, configuration loss, credential exposure, or network disruption resulting from its use. Always test on non-production equipment first.
