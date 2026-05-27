import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';

/// Service that abstracts camera and gallery operations.
/// Provides a unified API for taking photos and picking images.
class CameraService {
  final ImagePicker _picker = ImagePicker();

  /// Take a photo using the device camera.
  /// Returns the image file, or null if the user cancels.
  Future<File?> takePhoto({
    double? maxWidth = 1920,
    double? maxHeight = 2560,
    int imageQuality = 85,
    CameraDevice camera = CameraDevice.rear,
  }) async {
    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.camera,
        maxWidth: maxWidth,
        maxHeight: maxHeight,
        imageQuality: imageQuality,
        preferredCameraDevice: camera,
      );
      return photo != null ? File(photo.path) : null;
    } catch (e) {
      debugPrint('CameraService.takePhoto error: $e');
      return null;
    }
  }

  /// Pick an image from the device gallery.
  /// Returns the image file, or null if the user cancels.
  Future<File?> pickFromGallery({
    double? maxWidth = 1920,
    double? maxHeight = 2560,
    int imageQuality = 85,
  }) async {
    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: maxWidth,
        maxHeight: maxHeight,
        imageQuality: imageQuality,
      );
      return photo != null ? File(photo.path) : null;
    } catch (e) {
      debugPrint('CameraService.pickFromGallery error: $e');
      return null;
    }
  }

  /// Check if the device has a camera available.
  Future<bool> hasCamera() async {
    return _picker.supportsImageSource(ImageSource.camera);
  }
}
