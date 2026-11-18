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

  /// Trả lời mẫu cho ba câu hỏi gợi ý, khớp với trang mẫu [S.demoDescription].
  static final _answers = {
    S.askSuggestions[0]: 'Trang mẫu nói về cây xanh. Cây có ba bộ phận chính là rễ, thân và lá.',
    S.askSuggestions[1]:
        'Hình vẽ có ba phần. Dưới cùng là rễ cây, nằm trong đất. '
        'Ở giữa là thân cây. Trên cùng là các chiếc lá.',
    S.askSuggestions[2]:
        'Cây giống như một ngôi nhà ba tầng. Tầng dưới là rễ, hút nước từ đất. '
        'Tầng giữa là thân, đưa nước lên. Tầng trên là lá, đón ánh nắng để cây lớn lên.',
  };

  @override
  Future<ApiResult<DescribeResult>> describe(Uint8List image, {String pageType = 'auto'}) async {
    await Future<void>.delayed(delay);
    _counter++;
    return ApiOk(
      DescribeResult(
        imageId: 'demo${_counter.toString().padLeft(12, '0')}',
        description: S.demoDescription,
        pageType: pageType == 'auto' ? 'mixed' : pageType,
        unreadable: false,
        model: 'demo',
        promptVersion: 'demo',
        latencyMs: delay.inMilliseconds,
        cached: false,
      ),
    );
  }

  @override
  Future<ApiResult<AskResult>> ask(String imageId, String question, {List<AskTurn> history = const []}) async {
    await Future<void>.delayed(delay);
    final answer = _answers[question] ?? 'Đây là câu trả lời mẫu cho câu hỏi: $question';
    return ApiOk(AskResult(imageId: imageId, answer: answer, latencyMs: delay.inMilliseconds));
  }

  @override
  Future<ApiResult<HealthInfo>> health() async =>
      const ApiOk(HealthInfo(status: 'ok', vlmMode: 'demo', model: 'demo', sttMode: 'demo'));
}
