import 'dart:async';

import 'package:flutter/services.dart';

/// Cầu nối sang mã Android (MainActivity.kt):
/// - nhận sự kiện nút âm lượng để chụp,
/// - mở trang cài đặt giọng đọc của hệ thống.
class PlatformBridge {
  static const _keys = EventChannel('vn.nckh.sgbe/volume_keys');
  static const _methods = MethodChannel('vn.nckh.sgbe/system');

  Stream<String>? _volume;

  /// Mỗi lần bấm nút âm lượng phát ra `"up"` hoặc `"down"`.
  /// Chỉ khi màn hình chính đang lắng nghe thì nút âm lượng mới bị app giữ lại;
  /// ở màn hình khác nút vẫn chỉnh âm lượng bình thường.
  Stream<String> get volumeKeys =>
      _volume ??= _keys.receiveBroadcastStream().map((e) => e.toString()).handleError((_) {});

  Future<void> openTtsSettings() async {
    try {
      await _methods.invokeMethod<void>('openTtsSettings');
    } on PlatformException {
      // Máy không có trang này: bỏ qua, người dùng tự mở Cài đặt.
    } on MissingPluginException {
      // Đang chạy test hoặc không phải Android.
    }
  }
}
