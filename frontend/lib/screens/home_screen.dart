import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/audio_service.dart';
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
                  padding: const EdgeInsets.only(top: 24, left: 20, right: 20),
                  child: Row(
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Chào bạn 👋',
                            style: const TextStyle(
                              fontSize: 36,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'SgBe Vision',
                            style: TextStyle(
                              fontSize: 18,
                              color: const Color(0xFF8892B0),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                // ── Center: pulse-style greeting area ────
                const Expanded(
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // Glowing icon
                        _GlowingIcon(),
                        SizedBox(height: 16),
                        Text(
                          'Chạm để bắt đầu',
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        SizedBox(height: 8),
                        Text(
                          'Nói "Trợ giúp" để biết thêm',
                          style: TextStyle(
                            fontSize: 16,
                            color: Color(0xFF8892B0),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                // ── Quick actions row ────────────────────
                Padding(
                  padding:
                      const EdgeInsets.only(left: 20, right: 20, bottom: 16),
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
    return Container(
      width: 96,
      height: 96,
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
      child: const Icon(
        Icons.auto_awesome_rounded,
        size: 64,
        color: Color(0xFF00F0FF),
      ),
    );
  }
}
