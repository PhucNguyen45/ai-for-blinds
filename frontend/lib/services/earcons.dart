import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/services.dart';

/// Âm báo trạng thái: người dùng không nhìn màn hình nên cần nghe được app
/// đang làm gì. File âm do `tool/tao_am_bao.py` sinh ra.
enum Earcon {
  /// Chạm một lần: nghe tên nút.
  focus('audio/cham.wav'),

  /// Chạm hai lần: dùng nút.
  activate('audio/mo.wav'),
  shutter('audio/chup.wav'),
  waiting('audio/cho.wav'),
  done('audio/xong.wav'),
  error('audio/loi.wav');

  const Earcon(this.asset);
  final String asset;

  /// Âm của thao tác chạm phát trên kênh riêng, độ trễ thấp, không cắt âm trạng thái.
  bool get isUi => this == focus || this == activate;
}

abstract class EarconPlayer {
  Future<void> play(Earcon earcon);
}

class AudioEarconPlayer implements EarconPlayer {
  AudioEarconPlayer({bool Function()? enabled}) : _enabled = enabled ?? (() => true);

  final bool Function() _enabled;
  final AudioPlayer _status = AudioPlayer()..setReleaseMode(ReleaseMode.stop);
  final AudioPlayer _ui = AudioPlayer()
    ..setReleaseMode(ReleaseMode.stop)
    ..setPlayerMode(PlayerMode.lowLatency);

  @override
  Future<void> play(Earcon earcon) async {
    if (!_enabled()) return;
    final player = earcon.isUi ? _ui : _status;
    try {
      await player.stop();
      await player.play(AssetSource(earcon.asset));
    } catch (_) {
      // Âm báo chỉ là phụ; lỗi phát âm không được làm hỏng luồng đọc chính.
    }
  }
}

/// Rung phản hồi, tắt được trong Cài đặt. Mỗi tình huống một kiểu rung
/// để người dùng phân biệt bằng tay: chạm nhẹ, dùng nút, chụp, lỗi.
class Haptics {
  Haptics({bool Function()? enabled}) : _enabled = enabled ?? (() => true);

  final bool Function() _enabled;

  Future<void> focus() => _do(HapticFeedback.selectionClick);
  Future<void> activate() => _do(HapticFeedback.mediumImpact);
  Future<void> capture() => _do(HapticFeedback.heavyImpact);

  Future<void> error() async {
    if (!_enabled()) return;
    for (var i = 0; i < 3; i++) {
      await HapticFeedback.heavyImpact();
      await Future<void>.delayed(const Duration(milliseconds: 110));
    }
  }

  Future<void> _do(Future<void> Function() f) async {
    if (_enabled()) await f();
  }
}
