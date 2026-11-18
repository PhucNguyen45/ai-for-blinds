# Luật R8 cho bản release (bản debug không thu gọn mã nên không gặp).
#
# shared_preferences_android 2.5 gọi mã Kotlin từ Dart qua JNI, tìm hàm theo TÊN.
# R8 không thấy lời gọi nào trong mã Java/Kotlin nên xoá hoặc đổi tên các hàm đó
# -> NoSuchMethodError SharedPreferencesApiRegistrar.getAll, app treo ở màn hình chờ (ANR).
-keep class io.flutter.plugins.sharedpreferences.** { *; }
-keep class com.github.dart_lang.jni.** { *; }
# Phía JNI còn tìm theo tên cả lớp của Kotlin (kotlin.Result, Continuation...): giữ nguyên thư viện Kotlin.
-keep class kotlin.** { *; }
-keep class kotlinx.coroutines.** { *; }
-dontwarn kotlin.**
