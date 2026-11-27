/// Quyết định khi nào nhắc người dùng trong lúc đang ngắm máy. Không đụng tới camera, giọng đọc hay giao diện.
library;

import 'package:flutter/foundation.dart';

import 'frame_quality.dart';

/// Một tín hiệu cần phát: lời nhắc cho một lỗi, hoặc "khung hình đã ổn".
@immutable
class GuideSignal {
  const GuideSignal.hint(CaptureIssue this.issue);
  const GuideSignal.ready() : issue = null;

  final CaptureIssue? issue;
  bool get isReady => issue == null;

  @override
  bool operator ==(Object other) => other is GuideSignal && other.issue == issue;

  @override
  int get hashCode => issue.hashCode;

  @override
  String toString() => isReady ? 'ready' : 'hint(${issue!.name})';
}

/// Chống nhắc liên tục:
/// - một trạng thái phải kéo dài [persistFrames] khung mới được tính;
/// - cùng một lỗi chỉ nhắc lại sau [repeatAfter];
/// - "đã ổn" chỉ báo một lần, và chỉ báo lại sau khi đã từng hỏng đủ lâu.
class LiveGuide {
  LiveGuide({this.persistFrames = 3, this.repeatAfter = const Duration(seconds: 6)});

  final int persistFrames;
  final Duration repeatAfter;

  CaptureIssue? _current;
  int _count = 0;
  bool _readySent = false;
  CaptureIssue? _lastHint;
  Duration? _lastHintAt;

  GuideSignal? onFrame(CaptureIssue? issue, Duration now) {
    if (_count > 0 && issue == _current) {
      _count++;
    } else {
      _current = issue;
      _count = 1;
    }
    if (_count < persistFrames) return null;

    if (issue == null) {
      if (_readySent) return null;
      _readySent = true;
      _lastHint = null;
      return const GuideSignal.ready();
    }

    _readySent = false;
    final at = _lastHintAt;
    if (issue == _lastHint && at != null && now - at < repeatAfter) return null;
    _lastHint = issue;
    _lastHintAt = now;
    return GuideSignal.hint(issue);
  }

  void reset() {
    _current = null;
    _count = 0;
    _readySent = false;
    _lastHint = null;
    _lastHintAt = null;
  }
}

/// Chuyển chuỗi khung hình thành lỗi quan trọng nhất của từng khung.
/// Thứ tự ưu tiên: tối, rung (khi đang rung thì khung nhòe là hệ quả), rồi chói và mờ.
class FrameAnalyzer {
  FrameAnalyzer([this.thresholds = const FrameThresholds()]);

  final FrameThresholds thresholds;
  GrayImage? _previous;

  CaptureIssue? analyze(GrayImage frame) {
    final previous = _previous;
    _previous = frame;
    final issue = assess(measureGray(frame), thresholds);
    if (issue == CaptureIssue.dark) return issue;
    if (previous != null && frameDifference(previous, frame) >= thresholds.shakeDifference) {
      return CaptureIssue.shake;
    }
    return issue;
  }

  void reset() => _previous = null;
}
