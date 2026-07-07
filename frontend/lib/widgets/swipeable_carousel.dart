import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Full-screen vertical swipe carousel for browsing Learning Moments
/// (similar to TikTok/Reels UX adapted for blind users).
///
/// Uses [PageView.builder] with vertical scroll direction. Each page fills
/// the available space. Exposes [onPageChanged] callback and accessibility
/// semantics for screen-reader navigation.
class SwipeableCarousel extends StatefulWidget {
  /// Total number of pages.
  final int itemCount;

  /// Builder called for each page index.
  final IndexedWidgetBuilder itemBuilder;

  /// Called whenever the visible page changes.
  final ValueChanged<int> onPageChanged;

  /// Index of the initially visible page.
  final int initialIndex;

  const SwipeableCarousel({
    super.key,
    required this.itemCount,
    required this.itemBuilder,
    required this.onPageChanged,
    this.initialIndex = 0,
  });

  @override
  State<SwipeableCarousel> createState() => _SwipeableCarouselState();
}

class _SwipeableCarouselState extends State<SwipeableCarousel> {
  late final PageController _pageController;
  late int _currentIndex;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex;
    _pageController = PageController(initialPage: widget.initialIndex);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _onPageChanged(int index) {
    if (!mounted) return;
    setState(() => _currentIndex = index);
    widget.onPageChanged(index);
  }

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: 'Vuốt lên xuống để duyệt. Trang ${_currentIndex + 1} trên ${widget.itemCount}',
      child: PageView.builder(
        controller: _pageController,
        scrollDirection: Axis.vertical,
        itemCount: widget.itemCount,
        onPageChanged: _onPageChanged,
        itemBuilder: (context, index) {
          return LayoutBuilder(
            builder: (context, constraints) {
              return SizedBox(
                width: constraints.maxWidth,
                height: constraints.maxHeight,
                child: widget.itemBuilder(context, index),
              );
            },
          );
        },
      ),
    );
  }
}

/// Small vertical dots indicator on the right side of the carousel.
///
/// Displays [itemCount] dots as 8×8 circles with 6px gap.
/// The active dot is filled with [activeColor] and a soft glow;
/// inactive dots show only a border in [inactiveColor].
class CarouselPageIndicator extends StatelessWidget {
  /// Total number of dots.
  final int itemCount;

  /// Zero-based index of the active dot.
  final int currentIndex;

  /// Color of the active (current) dot.
  final Color activeColor;

  /// Color of inactive dots (border only).
  final Color inactiveColor;

  const CarouselPageIndicator({
    super.key,
    required this.itemCount,
    required this.currentIndex,
    this.activeColor = const Color(0xFF00F0FF),
    this.inactiveColor = const Color(0xFF1E2A4A),
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(itemCount, (i) {
        final bool isActive = i == currentIndex;
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 3),
          child: Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: isActive ? activeColor : Colors.transparent,
              border: Border.all(
                color: isActive ? activeColor : inactiveColor,
                width: 1.5,
              ),
              boxShadow: isActive
                  ? [
                      BoxShadow(
                        color: activeColor.withValues(alpha: 0.5),
                        blurRadius: 6,
                        spreadRadius: 1,
                      ),
                    ]
                  : null,
            ),
          ),
        );
      }),
    );
  }
}

/// Bottom action bar for carousel items with three neon-styled buttons.
///
/// Provides **Nghe lại** (Listen), **Xóa** (Delete), and **Chia sẻ** (Share)
/// controls with distinct neon colors. The bar sits in a semi-transparent
/// container matching the app's dark surface theme.
class CarouselControls extends StatelessWidget {
  /// Callback when the Listen button is pressed.
  final VoidCallback? onListen;

  /// Callback when the Delete button is pressed.
  final VoidCallback? onDelete;

  /// Callback when the Share button is pressed.
  final VoidCallback? onShare;

  const CarouselControls({
    super.key,
    this.onListen,
    this.onDelete,
    this.onShare,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF141829).withValues(alpha: 0.9),
      padding: const EdgeInsets.all(8),
      decoration: const BoxDecoration(
        border: Border(
          top: BorderSide(
            color: Color(0xFF1E2A4A),
            width: 1,
          ),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _ControlButton(
            icon: Icons.volume_up,
            label: 'Nghe lại',
            color: const Color(0xFF00F0FF),
            onTap: onListen,
          ),
          _ControlButton(
            icon: Icons.delete,
            label: 'Xóa',
            color: const Color(0xFFFF1744),
            onTap: onDelete,
          ),
          _ControlButton(
            icon: Icons.share,
            label: 'Chia sẻ',
            color: const Color(0xFF9D4EDD),
            onTap: onShare,
          ),
        ],
      ),
    );
  }
}

/// Internal small neon-styled control button used by [CarouselControls].
class _ControlButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback? onTap;

  const _ControlButton({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final bool enabled = onTap != null;
    return Semantics(
      button: true,
      label: label,
      hint: 'Nhấn hai lần để kích hoạt',
      child: GestureDetector(
        onTap: enabled
            ? () {
                HapticFeedback.mediumImpact();
                onTap!();
              }
            : null,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          width: 80,
          padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 4),
          decoration: BoxDecoration(
            color: color.withValues(alpha: enabled ? 0.15 : 0.05),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: color.withValues(alpha: enabled ? 0.6 : 0.15),
              width: 1,
            ),
            boxShadow: enabled
                ? [
                    BoxShadow(
                      color: color.withValues(alpha: 0.2),
                      blurRadius: 6,
                      spreadRadius: 1,
                    ),
                  ]
                : null,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                icon,
                size: 26,
                color: enabled ? color : color.withValues(alpha: 0.35),
              ),
              const SizedBox(height: 2),
              Text(
                label,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: enabled
                      ? const Color(0xFFFFFFFF)
                      : const Color(0xFFFFFFFF).withValues(alpha: 0.35),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
