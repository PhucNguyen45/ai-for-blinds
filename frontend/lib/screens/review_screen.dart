import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../models/learning_moment.dart';
import '../services/audio_service.dart';
import '../services/storage_service.dart';
import '../utils/responsive.dart';
import '../widgets/swipeable_carousel.dart';
import '../widgets/neon_button.dart';
import '../widgets/gradient_background.dart';

/// Neon Pulse review screen showing saved LearningMoments in a
/// vertical swipeable carousel (TikTok-style).
///
/// Features:
/// - Full-screen animated gradient background with ambient glow.
/// - Vertical swipe navigation through learning moments.
/// - Auto-speak moment title on page change.
/// - Listen, Delete controls per moment.
/// - Empty state with scan CTA.
class ReviewScreen extends StatefulWidget {
  const ReviewScreen({super.key});

  @override
  State<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends State<ReviewScreen> {
  final StorageService _storage = StorageService();
  List<LearningMoment> _moments = [];
  bool _isLoading = true;
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadMoments());
  }

  Future<void> _loadMoments() async {
    setState(() => _isLoading = true);
    try {
      final moments = await _storage.loadLearningMoments();
      if (mounted) {
        setState(() {
          _moments = moments
            ..sort((a, b) => b.createdAt.compareTo(a.createdAt));
          _currentIndex = 0;
          _isLoading = false;
        });
        // Auto-speak the first moment after loading.
        if (_moments.isNotEmpty) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (!mounted) return;
            final audio = context.read<AudioService>();
            audio.stop();
            audio.speak(_moments[0].title);
          });
        }
      }
    } catch (e) {
      debugPrint('ReviewScreen._loadMoments error: $e');
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _onPageChanged(int index) {
    setState(() => _currentIndex = index);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted || index >= _moments.length) return;
      final moment = _moments[index];
      final audio = context.read<AudioService>();
      audio.stop();
      audio.speak(moment.title);
    });
  }

  void _speakMoment(LearningMoment moment) {
    HapticFeedback.mediumImpact();
    final audio = context.read<AudioService>();
    audio.stop();
    final text = '${moment.title}. ${moment.description}';
    audio.speak(text);
  }

  Future<void> _deleteMoment(int index) async {
    HapticFeedback.mediumImpact();
    if (index >= _moments.length) return;

    setState(() {
      _moments.removeAt(index);
      if (_currentIndex >= _moments.length && _currentIndex > 0) {
        _currentIndex = _moments.length - 1;
      }
    });

    // Persist the updated list.
    final encoded = _moments.map((m) => m.toJson()).toList();
    await _storage.writeJson('learning_moments.json', encoded);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          const GradientBackground(showGlow: true),
          SafeArea(
            child: Column(
              children: [
                _buildTopBar(),
                Expanded(
                  child: _isLoading
                      ? const Center(child: CircularProgressIndicator())
                      : _moments.isEmpty
                          ? _buildEmptyState()
                          : _buildCarouselView(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTopBar() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Semantics(
            button: true,
            label: 'Quay lại',
            child: GestureDetector(
              onTap: () {
                HapticFeedback.mediumImpact();
                context.read<AudioService>().stop();
                Navigator.pop(context);
              },
              behavior: HitTestBehavior.opaque,
              child: const Padding(
                padding: EdgeInsets.all(8),
                child: Icon(
                  Icons.arrow_back_rounded,
                  size: 32,
                  color: Colors.white,
                ),
              ),
            ),
          ),
          const Spacer(),
          Flexible(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  'Ôn tập',
                  style: TextStyle(
                    fontSize: Responsive.textScale(context, 24, min: 18, max: 28),
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  'Vuốt lên/xuống để duyệt',
                  style: TextStyle(
                    fontSize: Responsive.textScale(context, 14, min: 12, max: 18),
                    color: Color(0xFF8892B0),
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Glowing icon container
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF8892B0).withValues(alpha: 0.2),
                    blurRadius: 20,
                    spreadRadius: 5,
                  ),
                ],
              ),
              child: const Icon(
                Icons.history,
                size: 80,
                color: Color(0xFF8892B0),
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'Chưa có khoảnh khắc học tập nào.',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Color(0xFF8892B0),
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            const Text(
              'Quét tài liệu hoặc đặt câu hỏi để bắt đầu.',
              style: TextStyle(
                fontSize: 16,
                color: Color(0xFF4A5580),
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            NeonButton(
              icon: Icons.camera_alt,
              label: 'Bắt đầu quét',
              color: const Color(0xFF00F0FF),
              onTap: () => Navigator.pushNamed(context, '/scanner'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCarouselView() {
    return Stack(
      children: [
        SwipeableCarousel(
          itemCount: _moments.length,
          itemBuilder: (context, index) =>
              _buildMomentPage(_moments[index], index),
          onPageChanged: _onPageChanged,
          initialIndex: _currentIndex,
        ),
        // Vertical page indicator on the right edge.
        Positioned(
          right: 8,
          top: 0,
          bottom: 0,
          child: Center(
            child: CarouselPageIndicator(
              itemCount: _moments.length,
              currentIndex: _currentIndex,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildMomentPage(LearningMoment moment, int index) {
    final bool hasImage = moment.imagePath != null;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Column(
        children: [
          // Scrollable content, vertically centered when short.
          Expanded(
            child: LayoutBuilder(
              builder: (context, constraints) {
                return SingleChildScrollView(
                  child: ConstrainedBox(
                    constraints: BoxConstraints(minHeight: constraints.maxHeight),
                    child: IntrinsicHeight(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          // Type indicator icon
                          Icon(
                            hasImage ? Icons.image_rounded : Icons.text_snippet,
                            size: Responsive.scale(context, 80, min: 60, max: 100),
                            color: const Color(0xFF00F0FF),
                          ),
                          const SizedBox(height: 24),
                          // Title
                          Text(
                            moment.title,
                            style: TextStyle(
                              fontSize:
                                  Responsive.textScale(context, 28, min: 22, max: 34),
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 12),
                          // Description
                          Text(
                            moment.description,
                            style: TextStyle(
                              fontSize:
                                  Responsive.textScale(context, 20, min: 16, max: 26),
                              color: Color(0xFF8892B0),
                            ),
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 16),
                          // Date
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(Icons.access_time, size: 16, color: Color(0xFF4A5580)),
                              const SizedBox(width: 4),
                              Text(
                                moment.formattedDate,
                                style: TextStyle(
                                  fontSize: Responsive.textScale(context, 16, min: 13, max: 20),
                                  color: Color(0xFF4A5580),
                                ),
                              ),
                            ],
                          ),
                          // Source text (only if available)
                          if (moment.sourceTextbook != null) ...[
                            const SizedBox(height: 8),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(Icons.menu_book, size: 16, color: Color(0xFF4A5580)),
                                const SizedBox(width: 4),
                                Flexible(
                                  child: Text(
                                    moment.sourceTextbook!,
                                    style: TextStyle(
                                      fontSize: Responsive.textScale(context, 16, min: 13, max: 20),
                                      color: Color(0xFF4A5580),
                                      fontStyle: FontStyle.italic,
                                    ),
                                    textAlign: TextAlign.center,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 12),
          // Bottom action controls
          CarouselControls(
            onListen: () => _speakMoment(moment),
            onDelete: () => _deleteMoment(index),
            onShare: null,
          ),
        ],
      ),
    );
  }
}
