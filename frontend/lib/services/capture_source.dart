import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

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

  /// Chọn ảnh có sẵn trong máy. Trả về `null` nếu người dùng huỷ.
  Future<Uint8List?> pickFromGallery();
}

class DeviceCaptureSource implements CaptureSource {
  /// 1920×1080: đủ nét cho chữ SGK, ảnh thường dưới 10 MB (giới hạn của máy chủ).
  static const resolution = ResolutionPreset.veryHigh;

  final ValueNotifier<CameraState> _state = ValueNotifier(CameraState.loading);
  CameraController? _controller;

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
        imageFormatGroup: ImageFormatGroup.jpeg,
      );
      await controller.initialize();
      await controller.setFlashMode(FlashMode.auto);
      _controller = controller;
      _state.value = CameraState.ready;
    } on CameraException catch (e) {
      _state.value = e.code.contains('Denied') ? CameraState.denied : CameraState.failed;
    }
  }

  @override
  Future<void> close() async {
    final c = _controller;
    _controller = null;
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
    final file = await c.takePicture();
    return file.readAsBytes();
  }

  @override
  Future<Uint8List?> pickFromGallery() async {
    final file = await ImagePicker().pickImage(source: ImageSource.gallery, maxWidth: 2400, imageQuality: 90);
    return file?.readAsBytes();
  }
}
