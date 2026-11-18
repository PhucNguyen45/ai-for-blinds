import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:sgbe/api/api_client.dart';
import 'package:sgbe/api/models.dart';
import 'package:sgbe/library/library_data.dart';
import 'package:sgbe/services/capture_source.dart';
import 'package:sgbe/services/earcons.dart';
import 'package:sgbe/services/platform_bridge.dart';
import 'package:sgbe/services/speech.dart';
import 'package:sgbe/services/speech_input.dart';

class FakeSpeaker implements Speaker {
  final spoken = <String>[];
  int stops = 0;
  double rate = 0.5;

  /// Khi đặt, câu nói chỉ "xong" khi completer này hoàn thành (giả lập câu dài).
  Completer<void>? hold;

  @override
  Future<bool> init({required double rate}) async => true;

  @override
  Future<void> speak(String text) async {
    spoken.add(text);
    final h = hold;
    if (h != null) await h.future;
  }

  @override
  Future<void> speakEnglish(String text) => speak(text);

  @override
  Future<void> stop() async {
    stops++;
    final h = hold;
    hold = null;
    if (h != null && !h.isCompleted) h.complete();
  }

  @override
  Future<void> setRate(double r) async => rate = r;
}

class FakeEarcons implements EarconPlayer {
  final played = <Earcon>[];

  @override
  Future<void> play(Earcon earcon) async => played.add(earcon);
}

class FakeApi implements SgbeApi {
  FakeApi({ApiResult<DescribeResult>? next}) : next = next ?? ok();

  ApiResult<DescribeResult> next;
  int describeCalls = 0;
  String? lastPageType;

  /// Khi đặt, `describe` chờ tới khi completer hoàn thành (giả lập máy chủ chậm).
  Completer<void>? gate;

  static ApiResult<DescribeResult> ok({String description = 'Trang có một lược đồ.', bool unreadable = false}) => ApiOk(
    DescribeResult(
      imageId: 'b9b1d4985e464bbb',
      description: description,
      pageType: 'map',
      unreadable: unreadable,
      model: 'mock',
      promptVersion: 'v1',
      latencyMs: 10,
      cached: false,
    ),
  );

  @override
  Future<ApiResult<DescribeResult>> describe(Uint8List image, {String pageType = 'auto'}) async {
    describeCalls++;
    lastPageType = pageType;
    final g = gate;
    if (g != null) await g.future;
    return next;
  }

  ApiResult<AskResult>? nextAsk;
  String? lastAskImageId;
  String? lastQuestion;
  List<AskTurn> lastHistory = const [];

  @override
  Future<ApiResult<AskResult>> ask(String imageId, String question, {List<AskTurn> history = const []}) async {
    lastAskImageId = imageId;
    lastQuestion = question;
    lastHistory = history;
    return nextAsk ?? ApiOk(AskResult(imageId: imageId, answer: 'Trả lời.', latencyMs: 1));
  }

  @override
  Future<ApiResult<HealthInfo>> health() async =>
      const ApiOk(HealthInfo(status: 'ok', vlmMode: 'mock', model: 'mock', sttMode: 'mock'));
}

class FakeCapture implements CaptureSource {
  FakeCapture({CameraState initial = CameraState.ready}) : _state = ValueNotifier(initial);

  final ValueNotifier<CameraState> _state;
  int pictures = 0;

  @override
  ValueListenable<CameraState> get state => _state;

  set cameraState(CameraState s) => _state.value = s;

  @override
  Future<void> open() async {}

  @override
  Future<void> close() async {}

  @override
  Widget preview() => const ColoredBox(color: Colors.black);

  @override
  Future<Uint8List?> takePicture() async {
    pictures++;
    return Uint8List.fromList([1, 2, 3]);
  }

  @override
  Future<Uint8List?> pickFromGallery() async => Uint8List.fromList([4, 5, 6]);
}

class FakeBridge extends PlatformBridge {
  final keys = StreamController<String>.broadcast();
  int ttsSettingsOpened = 0;

  @override
  Stream<String> get volumeKeys => keys.stream;

  @override
  Future<void> openTtsSettings() async => ttsSettingsOpened++;
}

class FakeLibrary implements LibrarySource {
  @override
  Future<List<Book>> load() async => const [
    Book(
      id: 'a',
      title: 'Sách A',
      subtitle: 'Lớp 3 · 2 trang mẫu',
      color: 'lib',
      pages: [
        BookPage(number: 1, title: 'Trang một', text: 'Nội dung trang một. Câu thứ hai.'),
        BookPage(number: 2, title: 'Trang hai', text: 'Nội dung trang hai.'),
      ],
    ),
    Book(
      id: 'b',
      title: 'Sách B',
      subtitle: 'Lớp 4 · 1 trang mẫu',
      color: 'ask',
      pages: [BookPage(number: 9, title: 'Trang chín', text: 'Nội dung trang chín.')],
    ),
  ];
}

/// Nhận giọng nói giả: trả lần lượt [results]; hết thì trả câu mặc định.
class FakeSpeechInput implements SpeechInput {
  FakeSpeechInput({this.ok = true});

  bool ok;
  final results = <SttResult>[];
  int listens = 0;
  int stops = 0;
  int cancels = 0;
  final partialCtl = StreamController<String>.broadcast();

  /// Khi đặt, listen() chờ tới khi stop()/cancel() (giả lập đang nghe).
  Completer<SttResult>? gate;

  /// false: stop() không đem lại kết quả (giả lập dịch vụ chờ mạng mãi).
  bool stopsComplete = true;

  static const macDinh = 'Hình vẽ có mấy phần?';

  SttResult _next() => results.isEmpty ? const SttText(macDinh) : results.removeAt(0);

  @override
  Future<bool> available() async => ok;

  @override
  Future<SttResult> listen() async {
    listens++;
    final g = gate;
    if (g != null) return g.future;
    return _next();
  }

  @override
  Future<void> stop() async {
    stops++;
    if (!stopsComplete) return;
    final g = gate;
    gate = null;
    if (g != null && !g.isCompleted) g.complete(_next());
  }

  @override
  Future<void> cancel() async {
    cancels++;
    final g = gate;
    gate = null;
    if (g != null && !g.isCompleted) g.complete(const SttCancelled());
  }

  @override
  Stream<String> get partials => partialCtl.stream;
}
