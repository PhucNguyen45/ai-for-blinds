import 'frame_quality.dart';
import 'live_guide.dart';

/// Nối chuỗi khung hình xem trước với lời nhắc: phân tích từng khung, chỉ phát tín hiệu khi đang ngắm máy
/// và app không bận nói.
class CaptureCoach {
  CaptureCoach({
    required this.aiming,
    required this.mayInterrupt,
    required this.onSignal,
    Duration Function()? clock,
    LiveGuide? guide,
  }) : _guide = guide ?? LiveGuide(),
       _clock = clock ?? (Stopwatch()..start()).elapsedClock;

  /// Người dùng đang ở màn hình ngắm máy. Rời đi thì đếm lại từ đầu.
  final bool Function() aiming;

  /// Lúc này được phép phát tín hiệu (app không đang nói). Chỉ hoãn, không đếm lại,
  /// để không lặp lời nhắc ngay sau mỗi câu nói.
  final bool Function() mayInterrupt;

  final void Function(GuideSignal signal) onSignal;
  final Duration Function() _clock;
  final LiveGuide _guide;
  final FrameAnalyzer _analyzer = FrameAnalyzer();

  void onFrame(GrayImage frame) {
    if (!aiming()) {
      _analyzer.reset();
      _guide.reset();
      return;
    }
    final issue = _analyzer.analyze(frame);
    if (!mayInterrupt()) return;
    final signal = _guide.onFrame(issue, _clock());
    if (signal != null) onSignal(signal);
  }
}

extension on Stopwatch {
  Duration elapsedClock() => elapsed;
}
