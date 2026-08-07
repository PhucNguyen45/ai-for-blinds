import 'package:flutter/material.dart';

class Responsive {
  static double scale(BuildContext context, double value,
      {double min = 0, double max = double.infinity}) {
    final width = MediaQuery.of(context).size.width;
    final ratio = (width / 414).clamp(0.7, 1.5);
    return (value * ratio).clamp(min, max);
  }

  static double textScale(BuildContext context, double base,
      {double min = 12, double max = 42}) {
    return base.clamp(min, max);
  }

  static double safeButtonSize(BuildContext context, double base,
      {double min = 100, double max = 200}) {
    final shortest = MediaQuery.of(context).size.shortestSide;
    return (shortest * (base / 414)).clamp(min, max);
  }
}
