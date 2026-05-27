import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../models/learning_moment.dart';
import '../services/audio_service.dart';
import '../services/storage_service.dart';
import '../theme/app_theme.dart';
import '../widgets/big_button.dart';

/// Review screen showing saved LearningMoments for revision.
/// Follows the SgBe Vision design spec:
/// - ListView of learning moments with image, question, answer summary
/// - Tap an item to hear the answer again via TTS
/// - Voice-first: select an item to listen
class ReviewScreen extends StatefulWidget {
  const ReviewScreen({super.key});

  @override
  State<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends State<ReviewScreen> {
  final StorageService _storage = StorageService();
  List<LearningMoment> _moments = [];
  bool _isLoading = true;

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
          _moments = moments..sort((a, b) => b.createdAt.compareTo(a.createdAt));
          _isLoading = false;
        });
      }
    } catch (e) {
      debugPrint('ReviewScreen._loadMoments error: $e');
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _speakMoment(LearningMoment moment) {
    HapticFeedback.mediumImpact();
    final audio = context.read<AudioService>();
    audio.stop();
    final text = '${moment.title}. ${moment.description}';
    audio.speak(text);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final bgColor = isDark ? AppTheme.pureBlack : AppTheme.pureWhite;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ôn tập'),
        backgroundColor: isDark ? AppTheme.pureBlack : AppTheme.primaryBlue,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, size: 32),
          onPressed: () {
            context.read<AudioService>().stop();
            Navigator.pop(context);
          },
        ),
      ),
      body: Container(
        color: bgColor,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _moments.isEmpty
                ? _buildEmptyState(theme)
                : _buildMomentList(theme, isDark),
      ),
    );
  }

  Widget _buildEmptyState(ThemeData theme) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.history_rounded,
              size: 80,
              color: Colors.grey.shade400,
            ),
            const SizedBox(height: 20),
            Text(
              'Chưa có khoảnh khắc học tập nào.',
              style: theme.textTheme.titleLarge,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            Text(
              'Quét tài liệu hoặc đặt câu hỏi để lưu lại kiến thức.',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: Colors.grey.shade500,
                height: 1.4,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            BigButton(
              icon: Icons.camera_alt_rounded,
              label: 'Bắt đầu quét tài liệu',
              color: AppTheme.primaryBlue,
              onTap: () => Navigator.pushNamed(context, '/scanner'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMomentList(ThemeData theme, bool isDark) {
    return Semantics(
      label: 'Danh sách khoảnh khắc học tập. ${_moments.length} mục.',
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _moments.length,
        itemBuilder: (context, index) {
          final moment = _moments[index];
          return _MomentCard(
            moment: moment,
            isDark: isDark,
            theme: theme,
            onTap: () => _speakMoment(moment),
          );
        },
      ),
    );
  }
}

class _MomentCard extends StatelessWidget {
  final LearningMoment moment;
  final bool isDark;
  final ThemeData theme;
  final VoidCallback onTap;

  const _MomentCard({
    required this.moment,
    required this.isDark,
    required this.theme,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final borderColor = isDark ? Colors.grey.shade700 : Colors.grey.shade300;
    final cardColor = isDark ? AppTheme.darkCard : AppTheme.pureWhite;

    return Semantics(
      button: true,
      label: '${moment.title}. ${moment.preview}. Lưu lúc ${moment.formattedDate}.',
      hint: 'Nhấn để nghe lại.',
      child: Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: GestureDetector(
          onTap: () {
            HapticFeedback.mediumImpact();
            onTap();
          },
          child: Container(
            decoration: BoxDecoration(
              color: cardColor,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: borderColor, width: 2),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Image thumbnail or placeholder
                Container(
                  width: 100,
                  height: 100,
                  decoration: BoxDecoration(
                    color: AppTheme.primaryBlue.withValues(alpha: 0.1),
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(14),
                      bottomLeft: Radius.circular(14),
                    ),
                  ),
                  child: Center(
                    child: Icon(
                      moment.imagePath != null
                          ? Icons.image_rounded
                          : Icons.text_snippet_rounded,
                      size: 40,
                      color: AppTheme.primaryBlue,
                    ),
                  ),
                ),
                // Content
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          moment.title,
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          moment.preview,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: isDark ? Colors.grey.shade400 : Colors.grey.shade600,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            Icon(
                              Icons.access_time_rounded,
                              size: 16,
                              color: Colors.grey.shade500,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              moment.formattedDate,
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.grey.shade500,
                              ),
                            ),
                            if (moment.sourceTextbook != null) ...[
                              const SizedBox(width: 12),
                              Icon(
                                Icons.menu_book_rounded,
                                size: 16,
                                color: Colors.grey.shade500,
                              ),
                              const SizedBox(width: 4),
                              Expanded(
                                child: Text(
                                  moment.sourceTextbook!,
                                  style: TextStyle(
                                    fontSize: 14,
                                    color: Colors.grey.shade500,
                                    fontStyle: FontStyle.italic,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                // Play button
                Padding(
                  padding: const EdgeInsets.all(8),
                  child: Icon(
                    Icons.volume_up_rounded,
                    size: 32,
                    color: AppTheme.accentGreen,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
