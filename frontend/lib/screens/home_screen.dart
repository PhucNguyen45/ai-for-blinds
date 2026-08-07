import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/audio_service.dart';
import '../utils/responsive.dart';
import '../widgets/neon_button.dart';
import '../widgets/gradient_background.dart';

/// Home screen — Neon Pulse Dashboard design.
///
/// Features:
/// - Animated gradient background with drifting glow circles
/// - Greeting header with app name
/// - Centered pulse-style icon area with "Chạm để bắt đầu" prompt
/// - Quick action row for scanning and voice Q&A
/// - TTS welcome message on first init
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _hasGreeted = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_hasGreeted) {
        _hasGreeted = true;
        final audio = context.read<AudioService>();
        audio.stop();
        audio.speak(
          'Chào mừng đến với SgBe Vision. Chạm để bắt đầu. Vuốt để chuyển trang.',
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final greetingS = Responsive.textScale(context, 36, min: 24, max: 42);
    final subS = Responsive.textScale(context, 18, min: 14, max: 22);
    final titleS = Responsive.textScale(context, 24, min: 18, max: 30);
    final hintS = Responsive.textScale(context, 16, min: 13, max: 20);
    final topPad = Responsive.scale(context, 24, min: 12, max: 32);
    final sidePad = Responsive.scale(context, 20, min: 12, max: 24);

    return Semantics(
      label: 'SgBe Vision. Chạm để bắt đầu. Vuốt để chuyển trang.',
      child: Stack(
        children: [
          // ── 1. Animated gradient background with glow ─────
          const GradientBackground(showGlow: true),

          // ── 2. Main content ────────────────────────────────
          SafeArea(
            child: Column(
              children: [
                // ── Top section: greeting header ─────────
                Padding(
                  padding: EdgeInsets.only(top: topPad, left: sidePad, right: sidePad),
                  child: Row(
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Chào bạn 👋',
                            style: TextStyle(
                              fontSize: greetingS,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'SgBe Vision',
                            style: TextStyle(
                              fontSize: subS,
                              color: const Color(0xFF8892B0),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                // ── Center: pulse-style greeting area ────
                Expanded(
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // Glowing icon
                        _GlowingIcon(),
                        const SizedBox(height: 16),
                        Text(
                          'Chạm để bắt đầu',
                          style: TextStyle(
                            fontSize: titleS,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Nói "Trợ giúp" để biết thêm',
                          style: TextStyle(
                            fontSize: hintS,
                            color: Color(0xFF8892B0),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                // ── Quick actions row ────────────────────
                Padding(
                  padding: EdgeInsets.only(
                    left: sidePad,
                    right: sidePad,
                    bottom: Responsive.scale(context, 16, min: 8, max: 24),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: NeonButton(
                          icon: Icons.document_scanner_rounded,
                          label: 'Quét tài liệu',
                          color: const Color(0xFF00F0FF),
                          onTap: () =>
                              Navigator.pushNamed(context, '/scanner'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: NeonButton(
                          icon: Icons.mic_rounded,
                          label: 'Hỏi đáp',
                          color: const Color(0xFF39FF14),
                          onTap: () =>
                              Navigator.pushNamed(context, '/voice-qa'),
                        ),
                      ),
                    ],
                  ),
                ),

                // ── Internet search action ─────────────────
                Padding(
                  padding: EdgeInsets.only(
                    left: sidePad,
                    right: sidePad,
                    bottom: Responsive.scale(context, 16, min: 8, max: 24),
                  ),
                  child: NeonButton(
                    icon: Icons.travel_explore_rounded,
                    label: 'Tìm kiếm thông tin',
                    subtitle: 'Tra cứu Internet bằng giọng nói',
                    color: const Color(0xFFFFB300),
                    onTap: () => Navigator.pushNamed(context, '/search'),
                  ),
                ),

                // ── Bottom section: "Gần đây" (placeholder) ──
                // Reserved for recent activity items when available.
                const SizedBox(height: 8),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Cyan glowing icon used in the center greeting area.
///
/// Displays [Icons.auto_awesome_rounded] inside a subtle circular
/// container with a soft cyan box shadow glow.
class _GlowingIcon extends StatelessWidget {
  const _GlowingIcon();

  @override
  Widget build(BuildContext context) {
    final size = Responsive.safeButtonSize(context, 96, min: 64, max: 120);
    final iconSize = size * 0.67;
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: const Color(0xFF00F0FF).withValues(alpha: 0.08),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF00F0FF).withValues(alpha: 0.35),
            blurRadius: 24,
            spreadRadius: 10,
          ),
        ],
      ),
      child: Icon(
        Icons.auto_awesome_rounded,
        size: iconSize,
        color: Color(0xFF00F0FF),
      ),
    );
  }
}
