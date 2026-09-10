# Bugfix Requirements Document

## Introduction

The Turing smart screen installer (`install_turing.sh`) has three related configuration/mapping bugs affecting USB screen ordering, default theme assignment, and theme filtering for the 10" screen. These bugs cause non-deterministic container assignment when both TURZX screens are connected, incorrect default themes for 3.5", 8.8", and 10" screens, and missing theme filtering for the 10" resolution class.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN both TURZX USB screens (PID 0x0088 and PID 0x0080) are connected THEN the system adds them to SCREEN_LIST in arbitrary sysfs enumeration order, causing non-deterministic container assignment (container 3 and 4 may swap depending on USB port)

1.2 WHEN a 3.5" screen is set up via `setup_additional_screen()` THEN the system does not assign any default theme (no case branch exists)

1.3 WHEN an 8.8" screen is set up via `setup_additional_screen()` THEN the system assigns "AMD" as the default theme instead of "8inchTheme2"

1.4 WHEN a 10" screen is set up via `setup_additional_screen()` THEN the system does not assign any default theme (no case branch exists for "10inch")

1.5 WHEN the embedded Python theme filter runs for a 10" screen THEN the system cannot match any themes because `SIZE_RESOLUTIONS` has no "10inch" entry, resulting in zero themes being copied

### Expected Behavior (Correct)

2.1 WHEN both TURZX USB screens (PID 0x0088 and PID 0x0080) are connected THEN the system SHALL sort SCREEN_LIST entries so PID 0x0088 (8.8") appears before PID 0x0080 (10"), giving deterministic assignment: container 3 = 8.8", container 4 = 10"

2.2 WHEN a 3.5" screen is set up via `setup_additional_screen()` THEN the system SHALL assign "Landscape6Grid" as the default theme

2.3 WHEN an 8.8" screen is set up via `setup_additional_screen()` THEN the system SHALL assign "8inchTheme2" as the default theme

2.4 WHEN a 10" screen is set up via `setup_additional_screen()` THEN the system SHALL assign "ColoredFlat_8inch" as the default theme

2.5 WHEN the embedded Python theme filter runs for a 10" screen THEN the system SHALL include "10inch" in `SIZE_RESOLUTIONS` with resolutions [(800, 1280), (1280, 800)] so that compatible themes are correctly copied

### Unchanged Behavior (Regression Prevention)

3.1 WHEN only a single TURZX USB screen is connected THEN the system SHALL CONTINUE TO detect and assign it to the correct container without any sorting side effects

3.2 WHEN serial-based screens (tty devices) are detected THEN the system SHALL CONTINUE TO enumerate them in the existing order without being affected by USB PID sorting

3.3 WHEN a 5" screen is set up via `setup_additional_screen()` THEN the system SHALL CONTINUE TO assign "PiSuite5" as the default theme

3.4 WHEN a 2.1" screen is set up via `setup_additional_screen()` THEN the system SHALL CONTINUE TO assign "26" as the default theme

3.5 WHEN the embedded Python theme filter runs for 3.5", 5", 8.8", or 2.1" screens THEN the system SHALL CONTINUE TO use their existing resolution entries unchanged

---

## Bug Condition (Formal)

### Bug Condition 1: PID Ordering

```pascal
FUNCTION isBugCondition_Ordering(X)
  INPUT: X of type ScreenDetectionState
  OUTPUT: boolean

  // Bug triggers when both TURZX PIDs are present in the USB scan
  RETURN "0088" IN X.detected_usb_pids AND "0080" IN X.detected_usb_pids
END FUNCTION
```

```pascal
// Property: Fix Checking - Deterministic PID Ordering
FOR ALL X WHERE isBugCondition_Ordering(X) DO
  result ← detect_screens'(X)
  ASSERT indexOf(result.SCREEN_LIST, pid="0088") < indexOf(result.SCREEN_LIST, pid="0080")
END FOR
```

### Bug Condition 2: Default Themes

```pascal
FUNCTION isBugCondition_Theme(X)
  INPUT: X of type ScreenSetup
  OUTPUT: boolean

  // Bug triggers for 3.5", 8.8", or 10" screens
  RETURN X.size IN {"3.5inch", "8.8inch", "10inch"}
END FUNCTION
```

```pascal
// Property: Fix Checking - Correct Default Themes
FOR ALL X WHERE isBugCondition_Theme(X) DO
  result ← setup_additional_screen'(X)
  ASSERT (X.size = "3.5inch" → result.theme = "Landscape6Grid")
     AND (X.size = "8.8inch" → result.theme = "8inchTheme2")
     AND (X.size = "10inch"  → result.theme = "ColoredFlat_8inch")
END FOR
```

### Bug Condition 3: SIZE_RESOLUTIONS Missing Entry

```pascal
FUNCTION isBugCondition_Resolution(X)
  INPUT: X of type ThemeFilterInput
  OUTPUT: boolean

  // Bug triggers when filtering themes for 10" screens
  RETURN X.target_size = "10inch"
END FUNCTION
```

```pascal
// Property: Fix Checking - 10inch Resolution Entry Exists
FOR ALL X WHERE isBugCondition_Resolution(X) DO
  result ← filter_themes'(X)
  ASSERT "10inch" IN result.SIZE_RESOLUTIONS
     AND result.SIZE_RESOLUTIONS["10inch"] = [(800, 1280), (1280, 800)]
END FOR
```

### Preservation Property

```pascal
// Property: Preservation Checking
FOR ALL X WHERE NOT isBugCondition_Ordering(X) AND NOT isBugCondition_Theme(X) AND NOT isBugCondition_Resolution(X) DO
  ASSERT F(X) = F'(X)
END FOR
```
