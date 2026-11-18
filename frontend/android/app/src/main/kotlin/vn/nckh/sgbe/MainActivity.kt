package vn.nckh.sgbe

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.view.KeyEvent
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodChannel

/**
 * Những việc phía Android mà Flutter không tự làm được:
 * 1. Nút âm lượng = nút chụp (màn hình chính) / nút nói (màn hình Hỏi). Chỉ giữ nút lại khi
 *    Flutter đang lắng nghe (volumeSink khác null); ở màn hình khác nút chỉnh âm lượng bình thường.
 * 2. Mở trang cài đặt giọng đọc (TTS) của hệ thống khi máy thiếu giọng tiếng Việt.
 * 3. Nhận giọng nói tiếng Việt bằng dịch vụ có sẵn của Android (SpeechRecognizer):
 *    không cần thư viện ngoài, có gói ngoại tuyến thì chạy không cần mạng.
 */
class MainActivity : FlutterActivity() {
    private var volumeSink: EventChannel.EventSink? = null

    private var recognizer: SpeechRecognizer? = null
    private var sttPending: MethodChannel.Result? = null
    private var sttPartials: EventChannel.EventSink? = null
    private var waitingMic: MethodChannel.Result? = null
    private var waitingLang = "vi-VN"

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

        EventChannel(messenger, "vn.nckh.sgbe/stt_partial").setStreamHandler(
            object : EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
                    sttPartials = events
                }

                override fun onCancel(arguments: Any?) {
                    sttPartials = null
                }
            },
        )

        MethodChannel(messenger, "vn.nckh.sgbe/stt").setMethodCallHandler { call, result ->
            when (call.method) {
                "available" -> result.success(SpeechRecognizer.isRecognitionAvailable(this))
                "listen" -> listen(result, call.argument<String>("lang") ?: "vi-VN")
                "stop" -> {
                    // Dừng thu âm, vẫn trả về phần đã nghe được.
                    recognizer?.stopListening()
                    result.success(null)
                }
                "cancel" -> {
                    recognizer?.cancel()
                    finishStt { it.success(null) }
                    result.success(null)
                }
                else -> result.notImplemented()
            }
        }
    }

    private fun listen(result: MethodChannel.Result, lang: String) {
        if (sttPending != null || waitingMic != null) {
            result.error("BUSY", "Đang nghe", null)
            return
        }
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            result.error("UNAVAILABLE", "Máy không có dịch vụ nhận giọng nói", null)
            return
        }
        if (Build.VERSION.SDK_INT >= 23 &&
            checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED
        ) {
            waitingMic = result
            waitingLang = lang
            requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), REQ_MIC)
            return
        }
        startStt(result, lang)
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode != REQ_MIC) return
        val r = waitingMic ?: return
        waitingMic = null
        if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            startStt(r, waitingLang)
        } else {
            r.error("PERMISSION", "Chưa được phép dùng micro", null)
        }
    }

    private fun startStt(result: MethodChannel.Result, lang: String) {
        sttPending = result
        val rec = recognizer ?: SpeechRecognizer.createSpeechRecognizer(this).also { recognizer = it }
        rec.setRecognitionListener(object : RecognitionListener {
            override fun onResults(results: Bundle?) {
                val text = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull() ?: ""
                finishStt { it.success(text) }
            }

            override fun onPartialResults(partialResults: Bundle?) {
                val text = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()
                if (!text.isNullOrBlank()) sttPartials?.success(text)
            }

            // Mã lỗi của Android (1 mạng chậm, 2 mạng, 6 im lặng, 7 không khớp, 9 quyền, 12-13 ngôn ngữ...)
            override fun onError(error: Int) = finishStt { it.error(error.toString(), null, null) }

            override fun onReadyForSpeech(params: Bundle?) {}
            override fun onBeginningOfSpeech() {}
            override fun onRmsChanged(rmsdB: Float) {}
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEndOfSpeech() {}
            override fun onEvent(eventType: Int, params: Bundle?) {}
        })
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, lang)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, packageName)
        }
        rec.startListening(intent)
    }

    /** Trả kết quả đúng một lần (Android có thể gọi onError sau onResults khi huỷ). */
    private fun finishStt(block: (MethodChannel.Result) -> Unit) {
        val r = sttPending ?: return
        sttPending = null
        block(r)
    }

    override fun onDestroy() {
        recognizer?.destroy()
        recognizer = null
        super.onDestroy()
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

    private companion object {
        const val REQ_MIC = 4201
    }
}
