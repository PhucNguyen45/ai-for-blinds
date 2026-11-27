import 'dart:async';

import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../capture/frame_quality.dart';

/// Kết quả mở camera.
enum CameraState { loading, ready, denied, missing, failed }

/// Nguồn ảnh của màn hình chính. Bản thật dùng camera trong app (chụp ngay,
/// không qua bước xác nhận của app camera hệ thống, vốn khó dùng khi không nhìn).
abstract class CaptureSource {
  ValueListenable<CameraState> get state;
  Future<void> open();
  Future<void> close();
  Widget preview();

  /// Chụp một ảnh. Trả về `null` nếu camera chưa sẵn sàng.
  Future<Uint8List?> takePicture();

  /// Nhận khung hình xem trước (ảnh xám đã thu nhỏ, vài khung mỗi giây) để nhắc người dùng; null = ngừng nhận.
  /// Vẫn giữ đăng ký khi camera đóng rồi mở lại.
  void watchFrames(void Function(GrayImage frame)? onFrame);

  /// Chọn ảnh có sẵn trong máy. Trả về `null` nếu người dùng huỷ.
  Future<Uint8List?> pickFromGallery();
}

class DeviceCaptureSource implements CaptureSource {
  /// 1920×1080: đủ nét cho chữ SGK, ảnh thường dưới 10 MB (giới hạn của máy chủ).
  static const resolution = ResolutionPreset.veryHigh;

  /// Khoảng cách tối thiểu giữa hai khung được phân tích, để đỡ tốn pin và không làm giật hình.
  static const frameInterval = Duration(milliseconds: 400);

  final ValueNotifier<CameraState> _state = ValueNotifier(CameraState.loading);
  CameraController? _controller;
  void Function(GrayImage frame)? _onFrame;
  bool _streaming = false;
  bool _paused = false;
  final Stopwatch _sinceFrame = Stopwatch()..start();

  @override
  void watchFrames(void Function(GrayImage frame)? onFrame) {
    _onFrame = onFrame;
    unawaited(_syncStream());
  }

  /// Bật hoặc tắt luồng khung hình cho khớp với việc có ai đang nhận hay không.
  /// Máy không hỗ trợ thì chỉ mất lời nhắc, chụp vẫn dùng được.
  Future<void> _syncStream() async {
    final c = _controller;
    if (c == null || !c.value.isInitialized) return;
    final want = _onFrame != null && !_paused;
    if (want == _streaming) return;
    _streaming = want;
    try {
      if (want) {
        await c.startImageStream(_handleFrame);
      } else {
        await c.stopImageStream();
      }
    } on CameraException {
      _streaming = false;
    }
  }

  void _handleFrame(CameraImage image) {
    final listener = _onFrame;
    if (listener == null || _sinceFrame.elapsed < frameInterval) return;
    _sinceFrame.reset();
    // Với định dạng YUV420, mặt phẳng đầu tiên là kênh sáng, đủ để đo tối, chói, mờ và rung.
    final plane = image.planes.first;
    listener(downscaleLuma(plane.bytes, width: image.width, height: image.height, rowStride: plane.bytesPerRow));
  }

  @override
  ValueListenable<CameraState> get state => _state;

  @override
  Future<void> open() async {
    if (_controller?.value.isInitialized ?? false) return;
    _state.value = CameraState.loading;
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        _state.value = CameraState.missing;
        return;
      }
      final back = cameras.firstWhere((c) => c.lensDirection == CameraLensDirection.back, orElse: () => cameras.first);
      final controller = CameraController(
        back,
        resolution,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.yuv420, // cho khung xem trước; ảnh chụp vẫn là JPEG
      );
      await controller.initialize();
      await controller.setFlashMode(FlashMode.auto);
      _controller = controller;
      _state.value = CameraState.ready;
      await _syncStream();
    } on CameraException catch (e) {
      _state.value = e.code.contains('Denied') ? CameraState.denied : CameraState.failed;
    }
  }

  @override
  Future<void> close() async {
    final c = _controller;
    _controller = null;
    _streaming = false;
    _state.value = CameraState.loading;
    await c?.dispose();
  }

  @override
  Widget preview() {
    final c = _controller;
    if (c == null || !c.value.isInitialized) return const ColoredBox(color: Colors.black);
    return FittedBox(
      fit: BoxFit.cover,
      clipBehavior: Clip.hardEdge,
      child: SizedBox(
        width: c.value.previewSize?.height ?? 1080,
        height: c.value.previewSize?.width ?? 1920,
        child: CameraPreview(c),
      ),
    );
  }

  @override
  Future<Uint8List?> takePicture() async {
    final c = _controller;
    if (c == null || !c.value.isInitialized || c.value.isTakingPicture) return null;
    // Một số máy không chụp được khi đang phát khung hình: tạm ngừng, chụp xong bật lại.
    _paused = true;
    await _syncStream();
    try {
      final file = await c.takePicture();
      return await file.readAsBytes();
    } finally {
      _paused = false;
      unawaited(_syncStream());
    }
  }

  @override
  Future<Uint8List?> pickFromGallery() async {
    final file = await ImagePicker().pickImage(source: ImageSource.gallery, maxWidth: 2400, imageQuality: 90);
    return file?.readAsBytes();
  }
}
