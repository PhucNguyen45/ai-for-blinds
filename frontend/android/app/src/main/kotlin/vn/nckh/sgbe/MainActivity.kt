package vn.nckh.sgbe

import android.content.Intent
import android.view.KeyEvent
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodChannel

/**
 * Hai việc phía Android mà Flutter không tự làm được:
 * 1. Nút âm lượng = nút chụp. Chỉ giữ nút lại khi màn hình chính đang lắng nghe
 *    (eventSink khác null); ở màn hình khác nút vẫn chỉnh âm lượng bình thường.
 * 2. Mở trang cài đặt giọng đọc (TTS) của hệ thống khi máy thiếu giọng tiếng Việt.
 */
class MainActivity : FlutterActivity() {
    private var volumeSink: EventChannel.EventSink? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        val messenger = flutterEngine.dartExecutor.binaryMessenger

        EventChannel(messenger, "vn.nckh.sgbe/volume_keys").setStreamHandler(
            object : EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
                    volumeSink = events
                }

                override fun onCancel(arguments: Any?) {
                    volumeSink = null
                }
            },
        )

        MethodChannel(messenger, "vn.nckh.sgbe/system").setMethodCallHandler { call, result ->
            when (call.method) {
                "openTtsSettings" -> {
                    try {
                        startActivity(Intent("com.android.settings.TTS_SETTINGS").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("UNAVAILABLE", e.message, null)
                    }
                }
                else -> result.notImplemented()
            }
        }
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent): Boolean {
        val sink = volumeSink
        val isVolume = keyCode == KeyEvent.KEYCODE_VOLUME_DOWN || keyCode == KeyEvent.KEYCODE_VOLUME_UP
        if (sink != null && isVolume) {
            // Giữ nút lâu chỉ tính một lần, tránh chụp liên tục.
            if (event.repeatCount == 0) {
                sink.success(if (keyCode == KeyEvent.KEYCODE_VOLUME_UP) "up" else "down")
            }
            return true
        }
        return super.onKeyDown(keyCode, event)
    }

    override fun onKeyUp(keyCode: Int, event: KeyEvent): Boolean {
        val isVolume = keyCode == KeyEvent.KEYCODE_VOLUME_DOWN || keyCode == KeyEvent.KEYCODE_VOLUME_UP
        if (volumeSink != null && isVolume) return true
        return super.onKeyUp(keyCode, event)
    }
}
