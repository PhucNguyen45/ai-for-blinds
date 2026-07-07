import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:sensors_plus/sensors_plus.dart';

// ---------------------------------------------------------------------------
// SwipeNavigator – lightweight gesture-only tab navigation
// ---------------------------------------------------------------------------

/// A lightweight gesture-driven navigation wrapper that detects horizontal
/// swipe gestures for app-wide tab navigation.
///
/// Wraps [child] in a [GestureDetector] that intercepts left/right swipes.
///   * Swipe left  (velocity < -300) → navigates to the next tab (index + 1).
///   * Swipe right (velocity >  300) → navigates to the previous tab (index - 1).
///
/// Tab indices are clamped to the range [0, 3] (matching the 4-tab layout:
/// home, scanner, Q&A, review).
class SwipeNavigator extends StatefulWidget {
  /// The child widget rendered beneath the gesture layer.
  final Widget child;

  /// Zero-based index of the currently active tab.
  final int currentIndex;

  /// Called when a swipe triggers a tab change.
  final ValueChanged<int> onNavigate;

  const SwipeNavigator({
    super.key,
    required this.child,
    required this.currentIndex,
    required this.onNavigate,
  });

  @override
  State<SwipeNavigator> createState() => _SwipeNavigatorState();
}

class _SwipeNavigatorState extends State<SwipeNavigator> {
  // -----------------------------------------------------------------------
  // Swipe handling
  // -----------------------------------------------------------------------

  void _onHorizontalDragEnd(DragEndDetails details) {
    final double velocity = details.primaryVelocity ?? 0;
    int nextIndex = widget.currentIndex;

    if (velocity < -300) {
      // Swipe left → next tab
      nextIndex = (widget.currentIndex + 1).clamp(0, 3);
    } else if (velocity > 300) {
      // Swipe right → previous tab
      nextIndex = (widget.currentIndex - 1).clamp(0, 3);
    } else {
      return; // velocity below threshold, ignore
    }

    if (nextIndex != widget.currentIndex) {
      HapticFeedback.mediumImpact();
      widget.onNavigate(nextIndex);
    }
  }

  // -----------------------------------------------------------------------
  // Build
  // -----------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: 'Vuốt trái phải để chuyển trang.',
      child: GestureDetector(
        onHorizontalDragEnd: _onHorizontalDragEnd,
        child: widget.child,
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// GestureNavigator – full-featured gesture + shake navigation
// ---------------------------------------------------------------------------

/// A gesture-driven navigation wrapper that intercepts swipe gestures and
/// shake events for app-wide navigation.
///
/// **Swipe navigation** (via [GestureDetector]):
///   * Swipe left  (velocity < -300) → navigates to the next tab (index + 1).
///   * Swipe right (velocity >  300) → navigates to the previous tab (index - 1).
///
/// **Long press** triggers [onVoiceCommand] (e.g. to activate voice assistant).
///
/// **Shake detection** (via [sensors_plus] accelerometer):
///   * When total acceleration exceeds [shakeThreshold] (default 30.0 m/s²),
///     [onVoiceCommand] is called.
///   * The accelerometer subscription starts on the first frame via
///     [WidgetsBinding.instance.addPostFrameCallback].
///   * If [sensors_plus] is not available the shake feature is silently skipped.
///
/// Tab indices are clamped to [0, 3] (home, scanner, Q&A, review).
class GestureNavigator extends StatefulWidget {
  /// The child widget rendered beneath the gesture layer.
  final Widget child;

  /// Zero-based index of the currently active tab.
  final int currentIndex;

  /// Called when a swipe triggers a tab change.
  final ValueChanged<int> onNavigate;

  /// Called on long-press or shake to activate voice-command mode.
  final VoidCallback onVoiceCommand;

  /// Minimum total acceleration (m/s²) to trigger a shake event.
  ///
  /// Defaults to 30.0. Lower values make detection more sensitive.
  final double shakeThreshold;

  const GestureNavigator({
    super.key,
    required this.child,
    required this.currentIndex,
    required this.onNavigate,
    required this.onVoiceCommand,
    this.shakeThreshold = 30.0,
  });

  @override
  State<GestureNavigator> createState() => _GestureNavigatorState();
}

class _GestureNavigatorState extends State<GestureNavigator> {
  StreamSubscription<dynamic>? _accelerometerSubscription;

  // -----------------------------------------------------------------------
  // Lifecycle
  // -----------------------------------------------------------------------

  @override
  void initState() {
    super.initState();
    // Start accelerometer subscription after the first frame so the widget
    // tree is fully built before we attempt the sensor import.
    WidgetsBinding.instance.addPostFrameCallback((_) => _initShakeDetection());
  }

  @override
  void dispose() {
    _accelerometerSubscription?.cancel();
    super.dispose();
  }

  // -----------------------------------------------------------------------
  // Shake detection (optional – sensors_plus may not be available)
  // -----------------------------------------------------------------------

  void _initShakeDetection() {
    try {
      // sensors_plus is listed in pubspec.yaml; if unavailable at runtime
      // (e.g. web or test environment) the import will throw.
      _accelerometerSubscription =
          accelerometerEventStream().listen(_onAccelerometerEvent);
    } catch (_) {
      // sensors_plus not available – shake detection disabled.
    }
  }

  void _onAccelerometerEvent(dynamic event) {
    // Compute total acceleration magnitude.
    final double x = (event.x as num).toDouble();
    final double y = (event.y as num).toDouble();
    final double z = (event.z as num).toDouble();
    final double total =
        (x * x + y * y + z * z); // squared magnitude (avoids sqrt)

    // Compare against squared threshold for efficiency.
    if (total > widget.shakeThreshold * widget.shakeThreshold) {
      widget.onVoiceCommand();
    }
  }

  // -----------------------------------------------------------------------
  // Gesture handling
  // -----------------------------------------------------------------------

  void _onHorizontalDragEnd(DragEndDetails details) {
    final double velocity = details.primaryVelocity ?? 0;
    int nextIndex = widget.currentIndex;

    if (velocity < -300) {
      // Swipe left → next tab
      nextIndex = (widget.currentIndex + 1).clamp(0, 3);
    } else if (velocity > 300) {
      // Swipe right → previous tab
      nextIndex = (widget.currentIndex - 1).clamp(0, 3);
    } else {
      return;
    }

    if (nextIndex != widget.currentIndex) {
      HapticFeedback.mediumImpact();
      widget.onNavigate(nextIndex);
    }
  }

  void _onLongPress() {
    HapticFeedback.heavyImpact();
    widget.onVoiceCommand();
  }

  // -----------------------------------------------------------------------
  // Build
  // -----------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: 'Vuốt trái phải để chuyển trang. Nhấn giữ để gọi giọng nói.',
      child: GestureDetector(
        onHorizontalDragEnd: _onHorizontalDragEnd,
        onLongPress: _onLongPress,
        child: widget.child,
      ),
    );
  }
}
