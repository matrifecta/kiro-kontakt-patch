the virtual machine boot was completely successful!You have correctly identified exactly where the issue lies with the turing.sh script for your secondary screen (Turing Smart Screen). The error Permission denied: OCI permission denied and the path /dev/vboxusb/... occur because your two systems are currently clashing over the same USB resource.the virtual machine boot was completely successful!You have correctly identified exactly where the issue lies with the turing.sh script for your secondary screen (Turing Smart Screen). The error Permission denied: OCI permission denied and the path /dev/vboxusb/... occur because your two systems are currently clashing over the same USB resource.# Turing Installer PID/Theme Bugfix Design

## Overview

Three related bugs in `install_turing.sh` cause non-deterministic USB screen ordering, incorrect default theme assignments, and missing theme resolution filtering for the 10" screen. The fix involves: (1) sorting TURZX USB entries by PID after detection to guarantee 0088 before 0080, (2) correcting the default theme case statement to cover 3.5", fix 8.8", and add 10", and (3) adding the missing "10inch" entry to the embedded Python `SIZE_RESOLUTIONS` dict.

## Glossary

- **Bug_Condition (C)**: The union of three conditions — both TURZX PIDs present (ordering bug), screen size in {3.5", 8.8", 10"} (theme bug), or target_size = "10inch" (resolution filter bug)
- **Property (P)**: Deterministic PID ordering (0088 < 0080), correct default themes per size, and successful theme filtering for 10"
- **Preservation**: Existing behavior for single-screen detection, serial screen ordering, 5" and 2.1" default themes, and theme filtering for non-10" sizes must remain unchanged
- **SCREEN_LIST**: Bash array in `detect_screens()` holding detected screens as `PORT:SERIAL:PRODUCT_ID` entries
- **SIZE_RESOLUTIONS**: Python dict in the embedded theme filter mapping size labels to acceptable resolution tuples
- **detect_screens()**: Function at ~line 2320 that populates SCREEN_LIST by scanning sysfs and /dev/tty devices
- **setup_additional_screen()**: Function at ~line 2583 that assigns default themes based on screen size

## Bug Details

### Bug Condition

The bugs manifest in three distinct code paths within `install_turing.sh`:

1. **PID Ordering**: When both TURZX USB screens (PID 0x0088 and 0x0080) are connected, sysfs enumeration order is non-deterministic, causing SCREEN_LIST to have unpredictable ordering of the two USB entries.

2. **Default Themes**: When `setup_additional_screen()` processes a 3.5", 8.8", or 10" screen, the case statement either maps to the wrong theme or has no branch at all.

3. **SIZE_RESOLUTIONS**: When the embedded Python theme filter receives `target_size = "10inch"`, it cannot find the key in the dict and returns an empty list, copying zero themes.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type InstallerState
  OUTPUT: boolean

  RETURN (input.context = "detect_screens" AND "0088" IN input.detected_pids AND "0080" IN input.detected_pids)
         OR (input.context = "setup_additional_screen" AND input.size IN {"3.5inch", "8.8inch", "10inch"})
         OR (input.context = "theme_filter" AND input.target_size = "10inch")
END FUNCTION
```

### Examples

- **PID Ordering**: Both screens connected via USB ports 3-1 and 3-2. Sysfs enumerates 0080 first → SCREEN_LIST = [..., "usb:3-2:serial:0080", "usb:3-1:serial:0088"]. Container 3 gets the 10" screen incorrectly. Expected: 0088 always before 0080.
- **3.5" Theme**: `setup_additional_screen()` called with SIZE="3.5inch" → falls through case with no match, no theme set. Expected: "Landscape6Grid".
- **8.8" Theme**: `setup_additional_screen()` called with SIZE="8.8inch" → sets "AMD". Expected: "8inchTheme2".
- **10" Theme**: `setup_additional_screen()` called with SIZE="10inch" → falls through case with no match. Expected: "ColoredFlat_8inch".
- **10" Resolution Filter**: Python filter called with target_size="10inch" → `SIZE_RESOLUTIONS.get("10inch", [])` returns `[]`, no themes match. Expected: returns `[(800, 1280), (1280, 800)]`.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Serial-based screen detection (tty devices) must continue to enumerate in /dev order without interference from USB sorting
- Single TURZX USB screen detection must work without side effects from the sorting logic
- 5" screen default theme ("PiSuite5") must remain unchanged
- 2.1" screen default theme ("26") must remain unchanged
- Theme filtering for 3.5", 5", 8.8", and 2.1" screens must use their existing SIZE_RESOLUTIONS entries unmodified
- The USB detection loop itself (vendor/product matching, busnum/devnum extraction) must remain unchanged

**Scope:**
All inputs that do NOT involve (a) both TURZX PIDs being present, (b) screen sizes 3.5"/8.8"/10" in the theme case, or (c) 10" in the Python filter should be completely unaffected by this fix. This includes:
- Single-screen setups
- Serial-only setups (Rev A/B/C/D)
- 5" and 2.1" theme assignments
- Theme filtering for non-10" sizes

## Hypothesized Root Cause

Based on the bug description and code analysis, the root causes are:

1. **PID Ordering — Uncontrolled sysfs iteration**: The `for usbdev in /sys/bus/usb/devices/*/idVendor` loop iterates in filesystem glob order, which is non-deterministic across boots and USB topologies. No post-processing sorts the resulting USB entries.

2. **Default Themes — Incomplete/incorrect case statement**: The `case "$SIZE"` block in `setup_additional_screen()` was written when only 5" and 2.1" screens existed. The 8.8" branch was added with "AMD" (likely a placeholder or wrong copy-paste). Branches for "3.5inch" and "10inch" were never added.

3. **SIZE_RESOLUTIONS — Omitted dict entry**: The embedded Python was written before the 10" screen existed (PID 0x0080). The dict was never updated to include the "10inch" resolution class.

## Correctness Properties

Property 1: Bug Condition - Deterministic PID Ordering

_For any_ installer state where both TURZX USB screens (PID 0x0088 and PID 0x0080) are detected, the fixed `detect_screens()` function SHALL produce a SCREEN_LIST where the entry with PID 0088 appears at a lower index than the entry with PID 0080, while all serial (tty) entries remain before USB entries in their original order.

**Validates: Requirements 2.1**

Property 2: Bug Condition - Correct Default Theme Assignment

_For any_ screen size in {"3.5inch", "8.8inch", "10inch"}, the fixed `setup_additional_screen()` function SHALL assign the correct default theme: "Landscape6Grid" for 3.5", "8inchTheme2" for 8.8", and "ColoredFlat_8inch" for 10".

**Validates: Requirements 2.2, 2.3, 2.4**

Property 3: Bug Condition - 10inch Resolution Entry Exists

_For any_ theme filter invocation with target_size = "10inch", the fixed embedded Python SHALL resolve SIZE_RESOLUTIONS["10inch"] to [(800, 1280), (1280, 800)], enabling correct theme matching.

**Validates: Requirements 2.5**

Property 4: Preservation - Serial and Single-Screen Detection

_For any_ input where the bug condition does NOT hold for ordering (single TURZX screen or no TURZX screens), the fixed `detect_screens()` function SHALL produce the same SCREEN_LIST as the original function, preserving serial-first ordering and single-screen behavior.

**Validates: Requirements 3.1, 3.2**

Property 5: Preservation - Existing Theme Assignments and Filtering

_For any_ screen size NOT in {"3.5inch", "8.8inch", "10inch"} (i.e., 5" and 2.1"), the fixed code SHALL produce the same default theme and the same theme filter behavior as the original code.

**Validates: Requirements 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

**File**: `install_turing.sh`

**Change 1: Sort TURZX USB entries after detection loop** (~line 2356, after the USB detection loop closes)

Add a post-processing block after the `done` that closes the USB detection loop:

1. **Separate serial and USB entries**: Iterate SCREEN_LIST, partition into `serial_entries` (those not starting with "usb:") and `usb_entries` (those starting with "usb:")
2. **Sort USB entries by PID**: Sort `usb_entries` so entries containing `:0088` come before entries containing `:0080`. Use a simple swap or `sort` with a custom key.
3. **Reconstruct SCREEN_LIST**: `SCREEN_LIST=("${serial_entries[@]}" "${sorted_usb_entries[@]}")`

```bash
# --- Sort USB entries: PID 0088 before 0080 for deterministic container assignment ---
local -a serial_entries=() usb_entries=()
for entry in "${SCREEN_LIST[@]}"; do
    if [[ "$entry" == usb:* ]]; then
        usb_entries+=("$entry")
    else
        serial_entries+=("$entry")
    fi
done
# Sort usb_entries: 0088 before 0080 (lower PID value first)
local -a sorted_usb=()
for entry in "${usb_entries[@]}"; do
    if [[ "$entry" == *:0088 ]]; then
        sorted_usb=("$entry" "${sorted_usb[@]}")
    else
        sorted_usb+=("$entry")
    fi
done
SCREEN_LIST=("${serial_entries[@]}" "${sorted_usb[@]}")
```

**Change 2: Fix default theme case statement** (~line 2583-2605)

Replace the existing case block with:

```bash
case "$SIZE" in
    "3.5inch")
        if [ -d "$INSTALL_DIR/res/themes/Landscape6Grid" ]; then
            sed -i "s|^  THEME:.*|  THEME: Landscape6Grid|" "$SCREEN_DIR/config.yaml"
            log_success "Screen $INDEX default theme: Landscape6Grid"
        fi
        ;;
    "5inch")
        if [ -d "$INSTALL_DIR/res/themes/PiSuite5" ]; then
            sed -i "s|^  THEME:.*|  THEME: PiSuite5|" "$SCREEN_DIR/config.yaml"
            log_success "Screen $INDEX default theme: PiSuite5"
        elif [ -d "$INSTALL_DIR/res/themes/5inchTheme2" ]; then
            sed -i "s|^  THEME:.*|  THEME: 5inchTheme2|" "$SCREEN_DIR/config.yaml"
        fi
        ;;
    "8.8inch")
        if [ -d "$INSTALL_DIR/res/themes/8inchTheme2" ]; then
            sed -i "s|^  THEME:.*|  THEME: 8inchTheme2|" "$SCREEN_DIR/config.yaml"
            log_success "Screen $INDEX default theme: 8inchTheme2"
        fi
        ;;
    "10inch")
        if [ -d "$INSTALL_DIR/res/themes/ColoredFlat_8inch" ]; then
            sed -i "s|^  THEME:.*|  THEME: ColoredFlat_8inch|" "$SCREEN_DIR/config.yaml"
            log_success "Screen $INDEX default theme: ColoredFlat_8inch"
        fi
        ;;
    "2.1inch")
        if [ -d "$INSTALL_DIR/res/themes/26" ]; then
            sed -i "s|^  THEME:.*|  THEME: 26|" "$SCREEN_DIR/config.yaml"
        fi
        ;;
esac
```

**Change 3: Add "10inch" to SIZE_RESOLUTIONS** (~line 2492)

Insert after the "8.8inch" entry:

```python
SIZE_RESOLUTIONS = {
    "3.5inch":  [(320, 480), (480, 320)],
    "5inch":    [(800, 480), (480, 800)],
    "8.8inch":  [(1920, 480), (480, 1920)],
    "10inch":   [(800, 1280), (1280, 800)],
    "2.1inch":  [(480, 480)],
}
```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bugs on unfixed code, then verify the fixes work correctly and preserve existing behavior. Since this is a bash script with an embedded Python snippet, testing uses both bash unit testing (bats or shell assertions) and Python unit tests.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bugs BEFORE implementing the fix. Confirm or refute the root cause analysis.

**Test Plan**: Extract the relevant functions into testable units. Mock sysfs paths and run `detect_screens()` with both PIDs present in various orders. Call the theme case logic with each buggy size. Invoke the Python filter with target_size="10inch".

**Test Cases**:
1. **PID Ordering Test**: Create mock sysfs with 0080 enumerated before 0088 → observe SCREEN_LIST has wrong order (will fail on unfixed code)
2. **3.5inch Theme Test**: Call setup with SIZE="3.5inch" → observe no theme assigned (will fail on unfixed code)
3. **8.8inch Theme Test**: Call setup with SIZE="8.8inch" → observe "AMD" assigned instead of "8inchTheme2" (will fail on unfixed code)
4. **10inch Theme Test**: Call setup with SIZE="10inch" → observe no theme assigned (will fail on unfixed code)
5. **10inch Filter Test**: Run Python filter with target_size="10inch" → observe zero themes copied (will fail on unfixed code)

**Expected Counterexamples**:
- SCREEN_LIST order is [0080, 0088] when sysfs enumerates 0080 first
- No theme written to config.yaml for 3.5" and 10"
- "AMD" written for 8.8" instead of "8inchTheme2"
- Python filter returns 0 matched themes for 10"

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed functions produce the expected behavior.

**Pseudocode:**
```
FOR ALL state WHERE isBugCondition(state) DO
  result := F'(state)
  IF state.context = "detect_screens":
    ASSERT indexOf(result.SCREEN_LIST, "0088") < indexOf(result.SCREEN_LIST, "0080")
  IF state.context = "setup_additional_screen":
    ASSERT theme_for(state.size) = expected_theme(state.size)
  IF state.context = "theme_filter":
    ASSERT "10inch" IN result.SIZE_RESOLUTIONS
    ASSERT result.SIZE_RESOLUTIONS["10inch"] = [(800,1280),(1280,800)]
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed functions produce the same result as the original.

**Pseudocode:**
```
FOR ALL state WHERE NOT isBugCondition(state) DO
  ASSERT F(state) = F'(state)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain (random screen counts, random USB topologies, random size strings)
- It catches edge cases that manual unit tests might miss (e.g., empty SCREEN_LIST, single USB entry)
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for single-screen detection, serial ordering, 5" and 2.1" themes, and non-10" filter runs, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Single USB Screen Preservation**: Verify that a single TURZX screen (either PID) is detected identically before and after the fix
2. **Serial Order Preservation**: Verify that serial entries maintain their /dev enumeration order unchanged
3. **5inch Theme Preservation**: Verify "PiSuite5" continues to be assigned for 5" screens
4. **2.1inch Theme Preservation**: Verify "26" continues to be assigned for 2.1" screens
5. **Non-10inch Filter Preservation**: Verify Python filter produces identical output for 3.5", 5", 8.8", 2.1" before and after fix

### Unit Tests

- Test PID sorting with both orderings (0088 first, 0080 first) → both produce 0088 before 0080
- Test PID sorting with only one PID present → no change
- Test PID sorting with no USB entries → no change
- Test each size in the theme case statement → correct theme assigned
- Test Python SIZE_RESOLUTIONS lookup for all five sizes → correct tuples returned

### Property-Based Tests

- Generate random SCREEN_LIST configurations (varying serial/USB counts, PID combinations) and verify ordering invariant holds
- Generate random size strings and verify theme assignment matches the expected mapping for known sizes, and does nothing for unknown sizes
- Generate random target_size values and verify SIZE_RESOLUTIONS returns correct tuples for all known sizes

### Integration Tests

- Full `detect_screens()` with mocked sysfs containing both PIDs in randomized order → verify container assignment
- Full `setup_additional_screen()` for each screen size → verify config.yaml updated correctly
- Full theme filter Python execution for each size → verify correct themes copied to destination
