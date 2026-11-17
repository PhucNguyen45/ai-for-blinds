import 'package:audioplayers/audioplayers.dart';

/// Âm báo trạng thái: người dùng không nhìn màn hình nên cần nghe được app
/// đang làm gì. File âm do `tool/tao_am_bao.py` sinh ra.
enum Earcon {
  shutter('audio/chup.wav'),
  waiting('audio/cho.wav'),
  done('audio/xong.wav'),
  error('audio/loi.wav');

  const Earcon(this.asset);
  final String asset;
}

abstract class EarconPlayer {
  Future<void> play(Earcon earcon);
}

class AudioEarconPlayer implements EarconPlayer {
  final AudioPlayer _player = AudioPlayer()..setReleaseMode(ReleaseMode.stop);

  @override
  Future<void> play(Earcon earcon) async {
    try {
      await _player.stop();
      await _player.play(AssetSource(earcon.asset));
    } catch (_) {
      // Âm báo chỉ là phụ; lỗi phát âm không được làm hỏng luồng đọc chính.
    }
  }
}
