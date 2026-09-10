# Implementation Plan: USB Audio Resume Hook

## Overview

Implement a POSIX shell-based systemd resume hook that performs USB unbind/rebind on configured audio devices after suspend. The implementation proceeds bottom-up: configuration and device scanning logic first, then unbind/rebind and audio restart, then the systemd unit, and finally the installer. All code is POSIX sh with no bashisms. Tests use bats-core.

## Tasks

- [ ] 1. Create the configuration file and core script skeleton
  - [ ] 1.1 Create the default configuration file (`usb-audio-resume.conf`)
    - Define `USB_ID`, `REBIND_DELAY`, and `RESTART_AUDIO` with commented defaults
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ] 1.2 Create `usb-audio-resume.sh` with shebang, logging helper, and configuration loader
    - Use `#!/bin/sh` shebang, no bashisms
    - Implement `log_info`, `log_warn`, `log_err` wrappers around `logger -t usb-audio-resume`
    - Implement `load_config` that sets defaults for `REBIND_DELAY=1` and `RESTART_AUDIO=false`, sources the config file, and validates `USB_ID` is set
    - Exit 1 with logged error if config file is missing or `USB_ID` is empty
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.1_

- [ ] 2. Implement device scanner and unbind/rebind engine
  - [ ] 2.1 Implement the device scanner function in `usb-audio-resume.sh`
    - Split `USB_ID` on `:` into vendor and product components
    - Iterate `/sys/bus/usb/devices/*/`, read `idVendor` and `idProduct` files
    - Collect matching directory basenames as Bus_IDs
    - Log warning and exit 0 if no devices match
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 2.2 Write property test for device matching correctness
    - **Property 1: Device matching correctness**
    - Create randomized mock sysfs trees with varying device counts, vendor IDs, and product IDs
    - Verify the scanner returns exactly the devices whose idVendor and idProduct match the target — no false positives, no false negatives
    - Use a bats-core test that generates random inputs in a loop (minimum 100 iterations)
    - **Validates: Requirements 1.1, 1.2, 1.3**

  - [ ] 2.3 Implement the unbind/rebind engine function in `usb-audio-resume.sh`
    - For each matched Bus_ID, write to `/sys/bus/usb/drivers/usb/unbind`
    - On unbind failure, log error with Bus_ID and skip rebind for that device
    - Sleep `REBIND_DELAY` seconds after successful unbind
    - Write Bus_ID to `/sys/bus/usb/drivers/usb/bind`
    - On bind failure, log error with Bus_ID
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 2.4 Write bats-core unit tests for config loader and device scanner
    - Test: config loads correctly with all variables set (4.1, 4.2, 4.3, 4.4)
    - Test: missing config file exits with error (4.5)
    - Test: missing USB_ID exits with error (4.2)
    - Test: default REBIND_DELAY is 1 when not set (4.3)
    - Test: default RESTART_AUDIO is false when not set (4.4)
    - Test: device scanner finds matching device in mock sysfs (1.1)
    - Test: device scanner returns empty for non-matching ID (1.2)
    - Test: Bus_ID extracted correctly from sysfs path (1.3)
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 3. Implement audio daemon restarter and wire main entry point
  - [ ] 3.1 Implement the audio daemon restart function in `usb-audio-resume.sh`
    - Check `RESTART_AUDIO` flag; skip entirely if `false`
    - Detect active user via `loginctl list-users --no-legend`
    - Run `systemctl --user --machine=<user>@.host restart pipewire wireplumber`
    - Log warning if no active user session found
    - Log error if restart command fails
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ] 3.2 Wire the main execution flow in `usb-audio-resume.sh`
    - Call `load_config`, then `scan_devices`, then `unbind_rebind` for each device, then `restart_audio`
    - Ensure the script is executable and self-contained
    - _Requirements: 1.1, 2.1, 3.1, 5.2, 5.3, 6.1, 6.2, 6.3_

  - [ ]* 3.3 Write bats-core unit tests for unbind/rebind and audio restart
    - Test: unbind failure skips rebind (2.4)
    - Test: bind failure logs error (2.5)
    - Test: RESTART_AUDIO=true triggers systemctl restart (3.1, 3.2)
    - Test: RESTART_AUDIO=false skips restart (3.3)
    - Test: all operations produce logger output with correct tag (6.1)
    - Test: success operations log at info level (6.2)
    - Test: failure operations log at error level with context (6.3)
    - _Requirements: 2.4, 2.5, 3.1, 3.2, 3.3, 6.1, 6.2, 6.3_

- [ ] 4. Checkpoint - Verify core script
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Create systemd service unit
  - [ ] 5.1 Create `usb-audio-resume.service`
    - Set `After=suspend.target hibernate.target hybrid-sleep.target suspend-then-hibernate.target`
    - Set `WantedBy=suspend.target hibernate.target hybrid-sleep.target suspend-then-hibernate.target`
    - Set `Type=oneshot` and `ExecStart=/usr/local/bin/usb-audio-resume.sh`
    - No `User=` directive (runs as root)
    - _Requirements: 5.1, 5.2, 5.3_

- [ ] 6. Create installer and uninstaller scripts
  - [ ] 6.1 Create `install.sh`
    - Copy `usb-audio-resume.sh` to `/usr/local/bin/` with executable permissions
    - Copy `usb-audio-resume.service` to `/etc/systemd/system/`
    - Copy `usb-audio-resume.conf` to `/etc/` only if it does not already exist (no overwrite)
    - Run `systemctl daemon-reload` and `systemctl enable usb-audio-resume.service`
    - Require root privileges, exit with error if not root
    - _Requirements: 7.1, 7.2_

  - [ ] 6.2 Create `uninstall.sh`
    - Run `systemctl disable usb-audio-resume.service`
    - Remove `/usr/local/bin/usb-audio-resume.sh`, `/etc/systemd/system/usb-audio-resume.service`
    - Optionally remove `/etc/usb-audio-resume.conf` (prompt or flag)
    - Run `systemctl daemon-reload`
    - Require root privileges, exit with error if not root
    - _Requirements: 7.3_

- [ ] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All scripts use POSIX sh (`#!/bin/sh`) with no bashisms
- Tests use bats-core for shell unit testing
- Property test (2.2) validates device matching with randomized mock sysfs trees
- The script runs as root via systemd; no user privilege escalation needed in the script itself
