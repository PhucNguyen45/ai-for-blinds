import 'package:flutter/material.dart';

/// Equalizer-style visualizer for voice settings.
///
/// Displays three groups of vertical bars representing [speed], [pitch],
/// and [volume] values, with filled bars glowing in the primary cyan color
/// and empty bars rendered in the border color.
class EQVisualizer extends StatelessWidget {
  /// Speech speed (0.2 = slowest, 1.0 = fastest).
  final double speed;

  /// Speech pitch (0.5 = lowest, 2.0 = highest).
  final double pitch;

  /// Speech volume (0.0 = silent, 1.0 = full).
  final double volume;

  const EQVisualizer({
    super.key,
    required this.speed,
    required this.pitch,
    required this.volume,
  }) : assert(speed >= 0.2 && speed <= 1.0),
       assert(pitch >= 0.5 && pitch <= 2.0),
       assert(volume >= 0.0 && volume <= 1.0);

  static const Color _primaryCyan = Color(0xFF00F0FF);
  static const Color _border = Color(0xFF1E2A4A);
  static const Color _surface = Color(0xFF141829);
  static const Color _textMuted = Color(0xFF8892B0);
  static const Color _white = Color(0xFFFFFFFF);

  static const int _barCount = 8;
  static const double _barWidth = 12;
  static const double _barMaxHeight = 60;
  static const double _barTopRadius = 4;

  /// Maps a value from its original range to a 0..8 bar count.
  static int _valueToBars(double value, double min, double max) {
    final clamped = value.clamp(min, max);
    final fraction = (clamped - min) / (max - min);
    return (fraction * _barCount).round().clamp(0, _barCount);
  }

  /// Builds a single bar with optional glow.
  static Widget _buildBar({required bool filled}) {
    return Container(
      width: _barWidth,
      height: _barMaxHeight,
      decoration: BoxDecoration(
        color: filled ? _primaryCyan : _border,
        borderRadius: const BorderRadius.vertical(
          top: Radius.circular(_barTopRadius),
        ),
        boxShadow: filled
            ? [
                BoxShadow(
                  color: _primaryCyan.withValues(alpha: 0.6),
                  blurRadius: 8,
                  spreadRadius: 1,
                ),
                BoxShadow(
                  color: _primaryCyan.withValues(alpha: 0.3),
                  blurRadius: 16,
                  spreadRadius: 2,
                ),
              ]
            : null,
      ),
    );
  }

  /// Builds one group: label, row of 8 bars, and value text.
  static Widget _buildGroup({
    required String label,
    required int filledBars,
    required String valueText,
  }) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Label
        Text(
          label,
          style: const TextStyle(
            fontSize: 16,
            color: _textMuted,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        // Bar row (bottom-aligned via reverse + vertical alignment tricks)
        SizedBox(
          height: _barMaxHeight,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: List.generate(_barCount, (i) {
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 2.5),
                child: Align(
                  alignment: Alignment.bottomCenter,
                  child: _buildBar(filled: i < filledBars),
                ),
              );
            }),
          ),
        ),
        const SizedBox(height: 6),
        // Value text
        Text(
          valueText,
          style: const TextStyle(
            fontSize: 16,
            color: _textMuted,
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final speedBars = _valueToBars(speed, 0.2, 1.0);
    final pitchBars = _valueToBars(pitch, 0.5, 2.0);
    final volumeBars = _valueToBars(volume, 0.0, 1.0);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _border, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Title
          const Text(
            'Giọng đọc hiện tại',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              color: _white,
            ),
          ),
          const SizedBox(height: 16),
          // Bar groups
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildGroup(
                label: 'Tốc độ',
                filledBars: speedBars,
                valueText: speed.toStringAsFixed(1),
              ),
              _buildGroup(
                label: 'Cao độ',
                filledBars: pitchBars,
                valueText: pitch.toStringAsFixed(1),
              ),
              _buildGroup(
                label: 'Âm lượng',
                filledBars: volumeBars,
                valueText: volume.toStringAsFixed(1),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
