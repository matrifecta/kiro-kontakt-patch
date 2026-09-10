# Requirements Document

## Introduction

After system suspend/resume on CachyOS (Arch-based Linux), external USB audio cards often fail to re-enumerate properly. The device appears dead until physically unplugged and replugged. This feature provides a systemd suspend/resume hook that performs a software-level USB unbind/rebind cycle on wake, forcing the kernel to re-enumerate the device without physical intervention. Optionally, the audio daemon (PipeWire/WirePlumber) can be restarted if the rebind alone is insufficient.

## Glossary

- **Resume_Hook**: A systemd system-sleep hook script that executes actions after the system wakes from suspend
- **USB_Audio_Device**: The external USB audio card identified by a vendor:product ID pair (e.g., `1234:5678`)
- **Unbind_Rebind**: The process of writing the device's bus ID to `/sys/bus/usb/drivers/usb/unbind` then `/sys/bus/usb/drivers/usb/bind`, forcing the kernel to re-enumerate the device
- **Audio_Daemon**: The user-space audio server (PipeWire and/or WirePlumber) responsible for managing audio routing
- **Vendor_Product_ID**: A colon-separated hexadecimal pair (e.g., `1234:abcd`) uniquely identifying a USB device model
- **Bus_ID**: The kernel's sysfs identifier for a USB device instance (e.g., `1-2` or `3-1.4`)

## Requirements

### Requirement 1: Device Detection

**User Story:** As a user, I want the resume hook to automatically find my USB audio card by its vendor:product ID, so that I don't have to hardcode sysfs bus paths that may change between boots.

#### Acceptance Criteria

1. WHEN the system resumes from suspend, THE Resume_Hook SHALL locate all USB devices matching the configured Vendor_Product_ID by scanning sysfs
2. IF no USB device matching the configured Vendor_Product_ID is found, THEN THE Resume_Hook SHALL log a warning message and exit without error
3. THE Resume_Hook SHALL derive the Bus_ID from the matching sysfs device path for use in unbind/rebind operations

### Requirement 2: USB Unbind/Rebind on Resume

**User Story:** As a user, I want the system to automatically perform a soft replug of my USB audio card after waking from sleep, so that the device works without physical intervention.

#### Acceptance Criteria

1. WHEN the system resumes from suspend and a matching USB_Audio_Device is detected, THE Resume_Hook SHALL write the Bus_ID to `/sys/bus/usb/drivers/usb/unbind`
2. WHEN the unbind operation completes, THE Resume_Hook SHALL wait a configurable delay (default 1 second) before rebinding
3. WHEN the delay elapses, THE Resume_Hook SHALL write the Bus_ID to `/sys/bus/usb/drivers/usb/bind`
4. IF the unbind operation fails, THEN THE Resume_Hook SHALL log an error message including the Bus_ID and skip the rebind for that device
5. IF the bind operation fails, THEN THE Resume_Hook SHALL log an error message including the Bus_ID

### Requirement 3: Audio Daemon Restart

**User Story:** As a user, I want the option to restart PipeWire/WirePlumber after the USB rebind, so that the audio stack fully re-initializes if the rebind alone is not sufficient.

#### Acceptance Criteria

1. WHERE the audio daemon restart option is enabled, THE Resume_Hook SHALL restart the Audio_Daemon after the rebind operation completes
2. WHERE the audio daemon restart option is enabled, THE Resume_Hook SHALL restart PipeWire and WirePlumber services for the active user session via `systemctl --user`
3. WHERE the audio daemon restart option is disabled, THE Resume_Hook SHALL skip audio daemon restart entirely
4. THE Resume_Hook SHALL default to having the audio daemon restart option disabled

### Requirement 4: Configuration

**User Story:** As a user, I want to configure the target device ID and behavior options in a single config file, so that I can adapt the hook to different hardware without editing the script.

#### Acceptance Criteria

1. THE Resume_Hook SHALL read configuration from `/etc/usb-audio-resume.conf`
2. THE Resume_Hook SHALL support a `USB_ID` variable specifying the Vendor_Product_ID to match
3. THE Resume_Hook SHALL support a `REBIND_DELAY` variable specifying the delay in seconds between unbind and rebind (default: 1)
4. THE Resume_Hook SHALL support a `RESTART_AUDIO` variable (true/false) controlling whether the Audio_Daemon is restarted (default: false)
5. IF the configuration file is missing, THEN THE Resume_Hook SHALL log an error and exit with a non-zero status

### Requirement 5: Systemd Integration

**User Story:** As a user, I want the hook to run automatically on every resume without manual intervention, so that my USB audio always works after waking from sleep.

#### Acceptance Criteria

1. THE Resume_Hook SHALL be triggered by systemd's suspend/resume lifecycle via a system-sleep hook or a systemd service with `After=suspend.target`
2. THE Resume_Hook SHALL execute only on the `post` (resume) phase of the sleep cycle, not on the `pre` (suspend) phase
3. THE Resume_Hook SHALL run with root privileges to access sysfs unbind/rebind interfaces

### Requirement 6: Logging and Diagnostics

**User Story:** As a user, I want the hook to log its actions to the system journal, so that I can diagnose issues if the audio device still fails after resume.

#### Acceptance Criteria

1. THE Resume_Hook SHALL log all actions (detection, unbind, rebind, daemon restart) to the systemd journal using a consistent identifier
2. WHEN an operation succeeds, THE Resume_Hook SHALL log a success message at informational level
3. WHEN an operation fails, THE Resume_Hook SHALL log a failure message at error level including relevant context (Bus_ID, error output)

### Requirement 7: Installation and Removal

**User Story:** As a user, I want a simple install/uninstall process, so that I can set up or remove the hook cleanly.

#### Acceptance Criteria

1. THE installation process SHALL place the hook script, systemd unit, and default configuration file in their correct system paths
2. THE installation process SHALL enable the systemd unit so the hook activates on next resume
3. THE removal process SHALL disable the systemd unit and remove installed files
