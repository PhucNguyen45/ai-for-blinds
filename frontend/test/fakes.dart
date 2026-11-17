import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:sgbe/api/api_client.dart';
import 'package:sgbe/api/models.dart';
import 'package:sgbe/services/capture_source.dart';
import 'package:sgbe/services/earcons.dart';
import 'package:sgbe/services/platform_bridge.dart';
import 'package:sgbe/services/speech.dart';

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

  static ApiResult<DescribeResult> ok({String description = 'Trang có một lược đồ.', bool unreadable = false}) =>
      ApiOk(DescribeResult(
        imageId: 'b9b1d4985e464bbb',
        description: description,
        pageType: 'map',
        unreadable: unreadable,
        model: 'mock',
        promptVersion: 'v1',
        latencyMs: 10,
        cached: false,
      ));

  @override
  Future<ApiResult<DescribeResult>> describe(Uint8List image, {String pageType = 'auto'}) async {
    describeCalls++;
    lastPageType = pageType;
    final g = gate;
    if (g != null) await g.future;
    return next;
  }

  @override
  Future<ApiResult<AskResult>> ask(String imageId, String question, {List<AskTurn> history = const []}) async =>
      ApiOk(AskResult(imageId: imageId, answer: 'Trả lời.', latencyMs: 1));

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
