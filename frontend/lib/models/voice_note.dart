class VoiceNote {
  final String id;
  final String filePath;
  final String title;
  final DateTime createdAt;
  final Duration duration;

  VoiceNote({
    required this.id,
    required this.filePath,
    required this.title,
    required this.createdAt,
    required this.duration,
  });

  /// Format duration as MM:SS.
  String get formattedDuration {
    final minutes = duration.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = duration.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  /// Format date as a readable string.
  String get formattedDate {
    final now = DateTime.now();
    final diff = now.difference(createdAt);

    if (diff.inMinutes < 1) return 'Vừa xong';
    if (diff.inHours < 1) return '${diff.inMinutes} phút trước';
    if (diff.inDays < 1) return '${diff.inHours} giờ trước';
    if (diff.inDays < 7) return '${diff.inDays} ngày trước';
    return 'Ngày ${createdAt.day} tháng ${createdAt.month} '
        'năm ${createdAt.year}';
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'filePath': filePath,
    'title': title,
    'createdAt': createdAt.toIso8601String(),
    'durationMs': duration.inMilliseconds,
  };

  factory VoiceNote.fromJson(Map<String, dynamic> json) => VoiceNote(
    id: json['id'] as String,
    filePath: json['filePath'] as String,
    title: json['title'] as String,
    createdAt: DateTime.parse(json['createdAt'] as String),
    duration: Duration(milliseconds: json['durationMs'] as int),
  );
}
