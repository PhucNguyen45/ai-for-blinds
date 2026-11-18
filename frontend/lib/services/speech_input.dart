import 'dart:async';

import 'package:flutter/services.dart';

import '../strings.dart';

/// Kết quả một lần nghe.
sealed class SttResult {
  const SttResult();
}

class SttText extends SttResult {
  const SttText(this.text);
  final String text;
}

/// Không nghe được: [message] là câu tiếng Việt đọc thẳng cho người dùng.
class SttFail extends SttResult {
  const SttFail(this.code, this.message);
  final String code;
  final String message;
}

/// Đã huỷ (người dùng rời màn hình).
class SttCancelled extends SttResult {
  const SttCancelled();
}

/// Nhận giọng nói. Tách giao diện để test không cần micro.
abstract class SpeechInput {
  /// Máy có dịch vụ nhận giọng nói không.
  Future<bool> available();

  /// Nghe một câu (tự dừng khi người dùng ngừng nói). Lần đầu Android hỏi quyền micro.
  Future<SttResult> listen();

  /// Dừng thu âm sớm, vẫn lấy phần đã nghe.
  Future<void> stop();

  Future<void> cancel();

  /// Chữ nghe được tạm thời trong lúc người dùng đang nói.
  Stream<String> get partials;
}

/// Dùng SpeechRecognizer có sẵn của Android (MainActivity.kt), tiếng Việt.
class AndroidSpeechInput implements SpeechInput {
  static const _methods = MethodChannel('vn.nckh.sgbe/stt');
  static const _partials = EventChannel('vn.nckh.sgbe/stt_partial');

  Stream<String>? _stream;

  @override
  Stream<String> get partials =>
      _stream ??= _partials.receiveBroadcastStream().map((e) => e.toString()).handleError((_) {});

  @override
  Future<bool> available() async {
    try {
      return await _methods.invokeMethod<bool>('available') ?? false;
    } on MissingPluginException {
      return false;
    } on PlatformException {
      return false;
    }
  }

  @override
  Future<SttResult> listen() async {
    try {
      final text = await _methods.invokeMethod<String>('listen', {'lang': 'vi-VN'});
      if (text == null) return const SttCancelled();
      if (text.trim().isEmpty) return SttFail('7', loiNhanGiong('7'));
      return SttText(text.trim());
    } on PlatformException catch (e) {
      return SttFail(e.code, loiNhanGiong(e.code));
    } on MissingPluginException {
      return SttFail('UNAVAILABLE', loiNhanGiong('UNAVAILABLE'));
    }
  }

  @override
  Future<void> stop() => _call('stop');

  @override
  Future<void> cancel() => _call('cancel');

  Future<void> _call(String m) async {
    try {
      await _methods.invokeMethod<void>(m);
    } on MissingPluginException {
      // test hoặc không phải Android
    } on PlatformException {
      // đã dừng
    }
  }
}

/// Mã lỗi SpeechRecognizer của Android -> câu nói cho người dùng.
String loiNhanGiong(String code) => switch (code) {
  '6' || '7' => S.sttNoMatch, // im lặng quá lâu / không khớp từ nào
  '1' || '2' || '4' => S.sttNetwork, // mạng chậm, mất mạng, máy chủ Google lỗi
  '9' || 'PERMISSION' => S.sttPermission,
  '12' || '13' => S.sttLanguage, // máy chưa có tiếng Việt
  '8' || 'BUSY' => S.sttBusy,
  'UNAVAILABLE' => S.sttUnavailable,
  _ => S.sttOther,
};
