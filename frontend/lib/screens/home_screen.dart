import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/audio_service.dart';
import '../theme/app_theme.dart';
import '../widgets/big_button.dart';

/// Home screen with 4 massive buttons for blind users.
/// Follows the SgBe Vision design spec:
/// - 4 nút: Quét tài liệu, Hỏi đáp kiến thức, Ôn tập, Cài đặt
/// - TTS tự động đọc "Chào mừng đến với SgBe Vision" khi mở app
/// - Voice-first: mọi tương tác đều có phản hồi âm thanh + rung
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
        audio.speak('Chào mừng đến với SgBe Vision. Hãy chọn một chức năng.');
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('SgBe Vision'),
        automaticallyImplyLeading: false,
      ),
      body: Semantics(
        label: 'SgBe Vision. Hãy chọn một chức năng.',
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            child: Column(
              children: [
                const Spacer(flex: 3),
                // Nút 1: 📷 Quét tài liệu
                BigButton(
                  icon: Icons.camera_alt_rounded,
                  label: 'Quét tài liệu',
                  subtitle: 'Chụp ảnh sách, tài liệu để đọc to',
                  color: AppTheme.primaryBlue,
                  onTap: () => Navigator.pushNamed(context, '/scanner'),
                ),
                const SizedBox(height: 14),
                // Nút 2: 🎤 Hỏi đáp kiến thức
                BigButton(
                  icon: Icons.mic_rounded,
                  label: 'Hỏi đáp kiến thức',
                  subtitle: 'Đặt câu hỏi bằng giọng nói, nhận câu trả lời',
                  color: AppTheme.accentGreen,
                  onTap: () => Navigator.pushNamed(context, '/voice-qa'),
                ),
                const SizedBox(height: 14),
                // Nút 3: 📚 Ôn tập
                BigButton(
                  icon: Icons.history_rounded,
                  label: 'Ôn tập',
                  subtitle: 'Xem lại các khoảnh khắc học tập đã lưu',
                  color: AppTheme.accentOrange,
                  onTap: () => Navigator.pushNamed(context, '/review'),
                ),
                const SizedBox(height: 14),
                // Nút 4: ⚙️ Cài đặt
                BigButton(
                  icon: Icons.settings_rounded,
                  label: 'Cài đặt',
                  subtitle: 'Tốc độ giọng, giao diện, ngôn ngữ',
                  color: AppTheme.primaryDark,
                  onTap: () => Navigator.pushNamed(context, '/settings'),
                ),
                const Spacer(flex: 1),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
