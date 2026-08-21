/// Represents a "learning moment" — a captured image, text, or note
/// that the student wants to remember and retrieve later.
/// Supports vector embeddings for semantic search (Persistent Visual Memory).
class LearningMoment {
  final String id;
  final String title;
  final String description;
  final String? imagePath;
  final String? textContent;
  final String? audioPath;
  final String? sourceTextbook;
  final DateTime createdAt;
  final List<double>? embedding;

  LearningMoment({
    required this.id,
    required this.title,
    required this.description,
    this.imagePath,
    this.textContent,
    this.audioPath,
    this.sourceTextbook,
    DateTime? createdAt,
    this.embedding,
  }) : createdAt = createdAt ?? DateTime.now();

  /// Format date as a readable relative string.
  String get formattedDate {
    final now = DateTime.now();
    final diff = now.difference(createdAt);

    // Đọc lên bằng TTS nên viết thành lời, không dùng ký hiệu tắt.
    if (diff.inMinutes < 1) return 'Vừa xong';
    if (diff.inHours < 1) return '${diff.inMinutes} phút trước';
    if (diff.inDays < 1) return '${diff.inHours} giờ trước';
    if (diff.inDays < 7) return '${diff.inDays} ngày trước';
    return 'Ngày ${createdAt.day} tháng ${createdAt.month} '
        'năm ${createdAt.year}';
  }

  /// Preview text (first 100 chars).
  String get preview {
    if (description.length > 100) {
      return '${description.substring(0, 100)}...';
    }
    return description;
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'description': description,
    'imagePath': imagePath,
    'textContent': textContent,
    'audioPath': audioPath,
    'sourceTextbook': sourceTextbook,
    'createdAt': createdAt.toIso8601String(),
    'embedding': embedding,
  };

  factory LearningMoment.fromJson(Map<String, dynamic> json) => LearningMoment(
    id: json['id'] as String,
    title: json['title'] as String? ?? '',
    description: json['description'] as String? ?? '',
    imagePath: json['imagePath'] as String?,
    textContent: json['textContent'] as String?,
    audioPath: json['audioPath'] as String?,
    sourceTextbook: json['sourceTextbook'] as String?,
    createdAt: json['createdAt'] != null
        ? DateTime.parse(json['createdAt'] as String)
        : null,
    embedding: json['embedding'] != null
        ? List<double>.from(json['embedding'] as List)
        : null,
  );
}
