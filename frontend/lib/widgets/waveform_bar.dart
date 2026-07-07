import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Enum representing the current state of the waveform visualization.
enum WaveformState {
  /// Static low-height bars in border color. No animation.
  idle,

  /// Randomized bar heights in lime green, updating every 300ms.
  active,

  /// Cyan sine wave sweeping left to right.
  processing,

  /// Brief red flash for 500ms, then returns to idle visual state.
  error,
}

/// An animated waveform visualization bar for audio processing/voice states.
///
/// Displays a series of vertical bars that animate based on the current
/// [WaveformState]:
/// - [idle]: 2px wide bars at 15% height in border color.
/// - [active]: 4px wide bars with randomized heights in lime green,
///   changing every 300ms.
/// - [processing]: 3px wide bars sweeping a sine wave in cyan from
///   left to right, driven by an [AnimationController] at 1.2s per cycle.
/// - [error]: Brief red flash (500ms) with idle-style bars, then
///   transitions to idle appearance.
class WaveformBar extends StatefulWidget {
  /// The current visual state of the waveform.
  final WaveformState state;

  /// Number of vertical bars to display. Defaults to 24.
  final int barCount;

  /// Total height of the widget in logical pixels. Defaults to 48.
  final double height;

  /// Optional override color. When null, each state uses its default color.
  final Color? customColor;

  const WaveformBar({
    super.key,
    required this.state,
    this.barCount = 24,
    this.height = 48,
    this.customColor,
  });

  @override
  State<WaveformBar> createState() => _WaveformBarState();
}

class _WaveformBarState extends State<WaveformBar>
    with TickerProviderStateMixin {
  late final AnimationController _controller;
  late List<double> _barHeights;

  Timer? _randomizeTimer;
  Timer? _errorTimer;
  bool _errorActive = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
    _barHeights = List.filled(widget.barCount, widget.height * 0.15);
    _syncToState(widget.state, oldState: null);
  }

  @override
  void didUpdateWidget(WaveformBar oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.barCount != widget.barCount) {
      _resizeBarHeights();
    }

    if (oldWidget.height != widget.height) {
      _rescaleBarHeights(oldWidget.height);
    }

    if (oldWidget.state != widget.state) {
      _syncToState(widget.state, oldState: oldWidget.state);
    }
  }

  /// Resizes [_barHeights] to match [widget.barCount],
  /// filling new entries with the idle height.
  void _resizeBarHeights() {
    final idleHeight = widget.height * 0.15;
    setState(() {
      if (widget.barCount > _barHeights.length) {
        _barHeights.addAll(
          List.filled(
            widget.barCount - _barHeights.length,
            idleHeight,
          ),
        );
      } else if (widget.barCount < _barHeights.length) {
        _barHeights = _barHeights.sublist(0, widget.barCount);
      }
    });
  }

  /// Scales existing bar heights when the widget height changes.
  void _rescaleBarHeights(double oldHeight) {
    final ratio = widget.height / oldHeight;
    setState(() {
      for (int i = 0; i < _barHeights.length; i++) {
        _barHeights[i] = (_barHeights[i] * ratio).clamp(
          0.0,
          widget.height,
        );
      }
    });
  }

  /// Synchronises internal state (timers, controller, bar heights) to
  /// [newState].
  void _syncToState(WaveformState newState, {WaveformState? oldState}) {
    // Always clean up previous transient state.
    _randomizeTimer?.cancel();
    _randomizeTimer = null;
    _errorTimer?.cancel();
    _errorTimer = null;
    _controller.removeListener(_onProcessingTick);

    switch (newState) {
      case WaveformState.idle:
        _errorActive = false;
        _controller.stop();
        _setIdleHeights();
        break;

      case WaveformState.active:
        _errorActive = false;
        _controller.stop();
        _randomizeHeights();
        _randomizeTimer = Timer.periodic(
          const Duration(milliseconds: 300),
          (_) => _randomizeHeights(),
        );
        break;

      case WaveformState.processing:
        _errorActive = false;
        _controller.addListener(_onProcessingTick);
        _controller.repeat();
        break;

      case WaveformState.error:
        _errorActive = true;
        _controller.stop();
        _setIdleHeights();
        _errorTimer = Timer(const Duration(milliseconds: 500), () {
          if (mounted) {
            setState(() {
              _errorActive = false;
            });
          }
        });
        break;
    }
  }

  /// Sets all bars to the idle height (15% of widget height).
  void _setIdleHeights() {
    setState(() {
      final h = widget.height * 0.15;
      for (int i = 0; i < _barHeights.length; i++) {
        _barHeights[i] = h;
      }
    });
  }

  /// Assigns random heights between 30% and 100% of widget height to each bar.
  void _randomizeHeights() {
    if (!mounted) return;
    final rng = math.Random();
    final minH = widget.height * 0.3;
    final range = widget.height * 0.7;
    setState(() {
      for (int i = 0; i < _barHeights.length; i++) {
        _barHeights[i] = minH + rng.nextDouble() * range;
      }
    });
  }

  /// Called on every animation tick during the [processing] state.
  /// Updates bars with a sine wave that sweeps across the display.
  void _onProcessingTick() {
    if (!mounted) return;
    setState(() {
      final phase = _controller.value * 2 * math.pi;
      for (int i = 0; i < _barHeights.length; i++) {
        final raw = math.sin(i * 0.5 - phase);
        _barHeights[i] = widget.height * (0.2 + 0.8 * math.max(0.0, raw));
      }
    });
  }

  @override
  void dispose() {
    _randomizeTimer?.cancel();
    _errorTimer?.cancel();
    _controller.removeListener(_onProcessingTick);
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    Color color;
    double barWidth;

    switch (widget.state) {
      case WaveformState.idle:
        color = widget.customColor ?? const Color(0xFF1E2A4A);
        barWidth = 2;
        break;
      case WaveformState.active:
        color = widget.customColor ?? const Color(0xFF39FF14);
        barWidth = 4;
        break;
      case WaveformState.processing:
        color = widget.customColor ?? const Color(0xFF00F0FF);
        barWidth = 3;
        break;
      case WaveformState.error:
        color = _errorActive
            ? (widget.customColor ?? const Color(0xFFFF1744))
            : (widget.customColor ?? const Color(0xFF1E2A4A));
        barWidth = 2;
        break;
    }

    return SizedBox(
      height: widget.height,
      width: double.infinity,
      child: RepaintBoundary(
        child: CustomPaint(
          painter: _WaveformPainter(
            barHeights: _barHeights,
            color: color,
            barWidth: barWidth,
            maxHeight: widget.height,
          ),
          size: Size(double.infinity, widget.height),
        ),
      ),
    );
  }
}

/// Custom painter that renders the vertical bars of the waveform.
///
/// Each bar is drawn as an [RRect] with rounded top corners (2px radius)
/// and flat bottom corners so they appear to originate from the canvas floor.
class _WaveformPainter extends CustomPainter {
  /// Height of each bar in logical pixels.
  final List<double> barHeights;

  /// Fill color for all bars.
  final Color color;

  /// Width of each bar in logical pixels.
  final double barWidth;

  /// Maximum height (the height of the canvas).
  final double maxHeight;

  const _WaveformPainter({
    required this.barHeights,
    required this.color,
    required this.barWidth,
    required this.maxHeight,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (barHeights.isEmpty) return;

    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    // Distribute bars evenly across the available width.
    final totalBarWidth = barWidth * barHeights.length;
    final spacing = size.width > totalBarWidth
        ? (size.width - totalBarWidth) / (barHeights.length + 1)
        : 2.0;

    const topRadius = Radius.circular(2);

    for (int i = 0; i < barHeights.length; i++) {
      final height = barHeights[i].clamp(0.0, maxHeight);
      if (height <= 0) continue;

      final x = spacing + i * (barWidth + spacing);
      final y = maxHeight - height;

      final rect = Rect.fromLTWH(x, y, barWidth, height);
      final rrect = RRect.fromRectAndCorners(
        rect,
        topLeft: topRadius,
        topRight: topRadius,
      );

      canvas.drawRRect(rrect, paint);
    }
  }

  @override
  bool shouldRepaint(_WaveformPainter oldDelegate) {
    return oldDelegate.barHeights != barHeights ||
        oldDelegate.color != color ||
        oldDelegate.barWidth != barWidth ||
        oldDelegate.maxHeight != maxHeight;
  }
}
