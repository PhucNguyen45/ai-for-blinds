import 'dart:typed_data';

import '../strings.dart';
import 'api_client.dart';
import 'models.dart';

/// Trả lời mẫu, không gửi ảnh đi đâu. Dùng để thử giao diện và âm báo
/// khi chưa có máy chủ, hoặc để người thử nghiệm làm quen app.
class DemoApi implements SgbeApi {
  DemoApi({this.delay = const Duration(milliseconds: 1500)});

  final Duration delay;
  int _counter = 0;

  @override
  Future<ApiResult<DescribeResult>> describe(Uint8List image, {String pageType = 'auto'}) async {
    await Future<void>.delayed(delay);
    _counter++;
    return ApiOk(DescribeResult(
      imageId: 'demo${_counter.toString().padLeft(12, '0')}',
      description: S.demoDescription,
      pageType: pageType == 'auto' ? 'mixed' : pageType,
      unreadable: false,
      model: 'demo',
      promptVersion: 'demo',
      latencyMs: delay.inMilliseconds,
      cached: false,
    ));
  }

  @override
  Future<ApiResult<AskResult>> ask(String imageId, String question, {List<AskTurn> history = const []}) async {
    await Future<void>.delayed(delay);
    return ApiOk(AskResult(
      imageId: imageId,
      answer: 'Đây là câu trả lời mẫu cho câu hỏi: $question',
      latencyMs: delay.inMilliseconds,
    ));
  }

  @override
  Future<ApiResult<HealthInfo>> health() async =>
      const ApiOk(HealthInfo(status: 'ok', vlmMode: 'demo', model: 'demo', sttMode: 'demo'));
}
