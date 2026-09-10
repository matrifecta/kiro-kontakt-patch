# Requirements Document

## Introduction

Turing Smart Screen Rev C displays running in Podman containers lose their USB TTY device after system suspend/resume on CachyOS (Arch-based Linux). The current recovery mechanism (`turing-resume.service`) power-cycles the entire parent USB hub, which kills all sibling devices (audio interfaces, other peripherals). This feature replaces the hub reset with a targeted, non-destructive recovery that monitors the screen's natural USB re-enumeration, updates container configuration if the TTY path changed, and restarts only the affected container(s).

## Glossary

- **Wake_Recovery_Service**: A user-level systemd service that monitors D-Bus for resume signals and orchestrates Turing display recovery without hub resets
- **Turing_Screen**: A Turing Smart Screen Rev C display managed by a Podman container, identified by its USB vendor:product ID
- **CH340_Controller**: The USB-serial chip on the Rev C screen; during suspend it presents as VID:PID `1a86:ca21`, on wake it re-enumerates with NXP gadget PIDs
- **TTY_Device**: The character device node (e.g., `/dev/ttyACM0`, `/dev/ttyUSB0`) created by the kernel when the screen's USB-serial controller enumerates
- **Container_Config**: The `config.yaml` file mounted into each Turing display container, containing a `COM_PORT` field that references the TTY_Device path
- **Display_Container**: A Podman container running the Turing System Monitor software, managed by a systemd user service (e.g., `turing-display-1.service`)
- **Resume_Signal**: The `org.freedesktop.login1.Manager.PrepareForSleep(false)` D-Bus signal emitted by logind when the system wakes from suspend
- **Known_PIDs**: The set of USB product IDs associated with the Rev C screen: `1a86:ca21` (sleep), `0525:a4a7`, `1d6b:0121`, `1d6b:0106` (awake)

## Requirements

### Requirement 1: Resume Detection

**User Story:** As a user, I want the recovery service to detect when my system wakes from suspend, so that the Turing screen recovery process begins automatically.

#### Acceptance Criteria

1. THE Wake_Recovery_Service SHALL monitor the system D-Bus for the Resume_Signal (`PrepareForSleep` with value `false`)
2. WHEN a Resume_Signal is received, THE Wake_Recovery_Service SHALL initiate the screen recovery sequence
3. THE Wake_Recovery_Service SHALL run as a user-level systemd service with `Restart=always` to survive crashes

### Requirement 2: TTY Re-enumeration Monitoring

**User Story:** As a user, I want the service to wait for my Turing screens to re-enumerate on their own after wake, so that no USB hub reset is needed.

#### Acceptance Criteria

1. WHEN the recovery sequence starts, THE Wake_Recovery_Service SHALL poll for TTY_Device nodes associated with Known_PIDs by scanning sysfs
2. THE Wake_Recovery_Service SHALL poll at 1-second intervals for a configurable timeout (default: 30 seconds)
3. WHEN a TTY_Device associated with a Known_PID appears, THE Wake_Recovery_Service SHALL record its device path
4. IF no TTY_Device appears within the timeout period, THEN THE Wake_Recovery_Service SHALL log a timeout error for that screen and skip its recovery

### Requirement 3: Container Config Update

**User Story:** As a user, I want the container config updated with the new TTY device path if it changed after wake, so that the Turing software connects to the correct serial port.

#### Acceptance Criteria

1. WHEN a TTY_Device is detected for a Turing_Screen, THE Wake_Recovery_Service SHALL read the corresponding Container_Config file
2. IF the detected TTY_Device path differs from the `COM_PORT` value in Container_Config, THEN THE Wake_Recovery_Service SHALL update the `COM_PORT` field to the new path
3. IF the detected TTY_Device path matches the existing `COM_PORT` value, THEN THE Wake_Recovery_Service SHALL leave the Container_Config unchanged
4. THE Wake_Recovery_Service SHALL preserve all other fields in Container_Config when updating `COM_PORT`

### Requirement 4: Container Restart

**User Story:** As a user, I want only the Turing display container(s) restarted after wake, so that they reconnect to the screen without disrupting other services.

#### Acceptance Criteria

1. WHEN the TTY_Device is confirmed available (and config updated if needed), THE Wake_Recovery_Service SHALL restart the corresponding Display_Container via its systemd user service
2. THE Wake_Recovery_Service SHALL restart each Display_Container independently (failure to restart one container does not block others)
3. IF the container restart fails, THEN THE Wake_Recovery_Service SHALL log an error including the service name and exit status

### Requirement 5: No USB Hub Manipulation

**User Story:** As a user, I want the recovery process to never touch USB hub authorized state, so that my other USB devices (audio interfaces, peripherals) remain connected.

#### Acceptance Criteria

1. THE Wake_Recovery_Service SHALL NOT write to any USB hub `authorized` sysfs file
2. THE Wake_Recovery_Service SHALL NOT perform unbind/rebind operations on USB hub devices
3. THE Wake_Recovery_Service SHALL rely solely on the Turing_Screen's natural USB re-enumeration after resume

### Requirement 6: Multi-Screen Support

**User Story:** As a user with multiple Turing screens, I want all screens recovered independently after wake, so that each screen comes back online regardless of the others.

#### Acceptance Criteria

1. THE Wake_Recovery_Service SHALL discover all connected Turing_Screen devices by matching Known_PIDs in sysfs
2. THE Wake_Recovery_Service SHALL maintain a mapping between each Turing_Screen and its corresponding Display_Container service
3. WHEN multiple Turing_Screen devices are detected, THE Wake_Recovery_Service SHALL perform recovery for each screen independently
4. IF one screen fails to re-enumerate, THEN THE Wake_Recovery_Service SHALL continue recovery for remaining screens

### Requirement 7: Configuration

**User Story:** As a user, I want to configure screen-to-container mappings and timeout values, so that I can adapt the recovery to my specific setup.

#### Acceptance Criteria

1. THE Wake_Recovery_Service SHALL read configuration from a file specifying the screen-to-service mapping
2. THE configuration SHALL support defining multiple screens with their associated container service name and config.yaml path
3. THE configuration SHALL support a `timeout` value specifying the maximum seconds to wait for TTY re-enumeration (default: 30)
4. IF the configuration file is missing or invalid, THEN THE Wake_Recovery_Service SHALL log an error and exit with a non-zero status

### Requirement 8: Logging and Diagnostics

**User Story:** As a user, I want the recovery service to log its actions, so that I can troubleshoot if a screen fails to recover.

#### Acceptance Criteria

1. THE Wake_Recovery_Service SHALL log all recovery actions (resume detected, polling started, TTY found, config updated, container restarted) to the systemd journal
2. WHEN an operation succeeds, THE Wake_Recovery_Service SHALL log a message at informational level
3. WHEN an operation fails or times out, THE Wake_Recovery_Service SHALL log a message at error level including relevant context (screen identifier, TTY path, timeout value)

### Requirement 9: Installation and Migration

**User Story:** As a user, I want the new recovery service to cleanly replace the old hub-reset approach, so that I don't have conflicting wake handlers.

#### Acceptance Criteria

1. THE installation process SHALL disable and remove the old `turing-resume.service` that performs USB hub resets
2. THE installation process SHALL remove the `/usr/local/bin/turing-usb-reset` script and its sudoers entry
3. THE installation process SHALL install and enable the new Wake_Recovery_Service as a systemd user service
4. THE installation process SHALL create a default configuration file with screen-to-service mappings detected from existing container services
