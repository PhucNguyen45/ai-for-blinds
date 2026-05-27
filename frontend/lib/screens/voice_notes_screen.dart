import 'dart:async';
import 'dart:io';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

import '../models/voice_note.dart';
import '../theme/app_theme.dart';
import '../widgets/big_button.dart';

/// Screen for recording/playing voice notes. Simplified for blind users.
class VoiceNotesScreen extends StatefulWidget {
  const VoiceNotesScreen({super.key});

  @override
  State<VoiceNotesScreen> createState() => _VoiceNotesScreenState();
}

class _VoiceNotesScreenState extends State<VoiceNotesScreen> {
  final AudioRecorder _recorder = AudioRecorder();
  final AudioPlayer _player = AudioPlayer();
  final List<VoiceNote> _notes = [];
  final Stopwatch _recordingTimer = Stopwatch();

  bool _isRecording = false;
  bool _isPlaying = false;
  String? _currentlyPlayingId;

  @override
  void initState() {
    super.initState();
    _loadNotes();
    _player.onPlayerComplete.listen((_) {
      if (mounted) {
        setState(() {
          _isPlaying = false;
          _currentlyPlayingId = null;
        });
      }
    });
  }

  @override
  void dispose() {
    _recorder.dispose();
    _player.dispose();
    super.dispose();
  }

  Future<void> _loadNotes() async {
    try {
      final dir = await _getNotesDirectory();
      if (!await dir.exists()) return;

      final files = dir.listSync().whereType<File>().toList();
      final notes = <VoiceNote>[];

      for (final file in files) {
        if (file.path.endsWith('.m4a')) {
          final stat = file.statSync();
          notes.add(VoiceNote(
            id: file.path,
            filePath: file.path,
            title: 'Study Note',
            createdAt: stat.modified,
            duration: const Duration(seconds: 0),
          ));
        }
      }

      notes.sort((a, b) => b.createdAt.compareTo(a.createdAt));
      if (mounted) setState(() => _notes..clear()..addAll(notes));
    } catch (e) {
      debugPrint('Error loading notes: $e');
    }
  }

  Future<Directory> _getNotesDirectory() async {
    final appDir = await getApplicationDocumentsDirectory();
    final notesDir = Directory('${appDir.path}/voice_notes');
    if (!await notesDir.exists()) {
      await notesDir.create(recursive: true);
    }
    return notesDir;
  }

  Future<void> _startRecording() async {
    try {
      final hasPermission = await _recorder.hasPermission();
      if (!hasPermission) {
        _showSnackBar('Microphone permission required.');
        return;
      }

      final dir = await _getNotesDirectory();
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final path = '${dir.path}/note_$timestamp.m4a';

      await _recorder.start(
        const RecordConfig(encoder: AudioEncoder.aacLc, bitRate: 128000, sampleRate: 44100),
        path: path,
      );

      _recordingTimer.start();
      if (mounted) {
        setState(() => _isRecording = true);
        HapticFeedback.mediumImpact();
      }
    } catch (e) {
      debugPrint('Error starting recording: $e');
      _showSnackBar('Failed to start recording.');
    }
  }

  Future<void> _stopRecording() async {
    try {
      _recordingTimer.stop();
      final elapsed = _recordingTimer.elapsed;
      _recordingTimer.reset();

      final path = await _recorder.stop();
      if (path != null && await File(path).exists()) {
        await _finalizeRecording(path, elapsed);
      }
      if (mounted) setState(() => _isRecording = false);
    } catch (e) {
      debugPrint('Error stopping recording: $e');
      _recordingTimer.reset();
      if (mounted) setState(() => _isRecording = false);
    }
  }

  Future<void> _finalizeRecording(String path, Duration duration) async {
    try {
      final file = File(path);
      if (!await file.exists()) return;

      final title = 'Study Note - ${DateFormat('MMM d, h:mm a').format(DateTime.now())}';
      final note = VoiceNote(
        id: path,
        filePath: path,
        title: title,
        createdAt: DateTime.now(),
        duration: duration,
      );

      if (mounted) {
        setState(() => _notes.insert(0, note));
        HapticFeedback.heavyImpact();
        _showSnackBar('Recording saved!');
      }
    } catch (e) {
      debugPrint('Error finalizing recording: $e');
    }
  }

  Future<void> _playNote(VoiceNote note) async {
    try {
      final file = File(note.filePath);
      if (!await file.exists()) {
        _showSnackBar('File not found.');
        return;
      }

      if (_isPlaying && _currentlyPlayingId == note.id) {
        await _player.stop();
        if (mounted) setState(() { _isPlaying = false; _currentlyPlayingId = null; });
        return;
      }

      if (_isPlaying) await _player.stop();

      await _player.play(DeviceFileSource(note.filePath));
      if (mounted) {
        setState(() { _isPlaying = true; _currentlyPlayingId = note.id; });
        HapticFeedback.lightImpact();
      }
    } catch (e) {
      debugPrint('Error playing note: $e');
      _showSnackBar('Failed to play recording.');
    }
  }

  Future<void> _deleteNote(VoiceNote note) async {
    try {
      if (_currentlyPlayingId == note.id) {
        await _player.stop();
        _isPlaying = false;
        _currentlyPlayingId = null;
      }
      final file = File(note.filePath);
      if (await file.exists()) await file.delete();
      if (mounted) {
        setState(() => _notes.remove(note));
        HapticFeedback.lightImpact();
        _showSnackBar('Note deleted.');
      }
    } catch (e) {
      debugPrint('Error deleting note: $e');
      _showSnackBar('Failed to delete note.');
    }
  }

  void _showSnackBar(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), duration: const Duration(seconds: 2)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final bgColor = isDark ? AppTheme.pureBlack : AppTheme.pureWhite;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Voice Notes'),
        backgroundColor: isDark ? AppTheme.pureBlack : AppTheme.primaryBlue,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, size: 32),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Container(
        color: bgColor,
        child: Column(
          children: [
            // Record button
            Container(
              padding: const EdgeInsets.symmetric(vertical: 24),
              color: isDark ? AppTheme.darkCard : Colors.grey.shade50,
              child: Column(
                children: [
                  BigCircleButton(
                    icon: _isRecording ? Icons.stop_rounded : Icons.mic_rounded,
                    label: _isRecording ? 'Stop recording' : 'Start recording',
                    color: _isRecording ? AppTheme.accentRed : AppTheme.accentGreen,
                    onTap: _isRecording ? _stopRecording : _startRecording,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    _isRecording ? 'Recording...' : 'Tap to record',
                    style: theme.textTheme.titleMedium?.copyWith(
                      color: _isRecording ? AppTheme.accentRed : null,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 8),

            // Notes list
            Expanded(
              child: _notes.isEmpty
                  ? Center(
                      child: Text(
                        'No notes yet. Tap the button to record.',
                        style: theme.textTheme.bodyLarge?.copyWith(
                          color: Colors.grey.shade500,
                        ),
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      itemCount: _notes.length,
                      itemBuilder: (context, index) {
                        final note = _notes[index];
                        final isThisPlaying = _currentlyPlayingId == note.id && _isPlaying;

                        return Semantics(
                          label: '${note.title}. ${note.formattedDate}',
                          child: Container(
                            margin: const EdgeInsets.only(bottom: 8),
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                            decoration: BoxDecoration(
                              color: isDark ? AppTheme.darkCard : AppTheme.pureWhite,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                color: isThisPlaying
                                    ? AppTheme.accentGreen
                                    : (isDark ? Colors.grey.shade700 : Colors.grey.shade300),
                                width: isThisPlaying ? 2 : 1,
                              ),
                            ),
                            child: Row(
                              children: [
                                Expanded(
                                  child: GestureDetector(
                                    onTap: () => _playNote(note),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          note.title,
                                          style: theme.textTheme.titleMedium?.copyWith(
                                            fontWeight: FontWeight.w500,
                                          ),
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                        const SizedBox(height: 2),
                                        Text(
                                          note.formattedDate,
                                          style: theme.textTheme.bodyMedium?.copyWith(
                                            color: isDark ? Colors.grey.shade400 : Colors.grey.shade600,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                                Semantics(
                                  button: true,
                                  label: isThisPlaying ? 'Stop' : 'Play',
                                  child: GestureDetector(
                                    onTap: () => _playNote(note),
                                    child: Container(
                                      padding: const EdgeInsets.all(12),
                                      child: Icon(
                                        isThisPlaying
                                            ? Icons.stop_rounded
                                            : Icons.play_arrow_rounded,
                                        size: 36,
                                        color: isThisPlaying
                                            ? AppTheme.accentRed
                                            : AppTheme.accentGreen,
                                      ),
                                    ),
                                  ),
                                ),
                                Semantics(
                                  button: true,
                                  label: 'Delete note',
                                  child: GestureDetector(
                                    onTap: () => _deleteNote(note),
                                    child: Container(
                                      padding: const EdgeInsets.all(12),
                                      child: const Icon(
                                        Icons.delete_outline_rounded,
                                        size: 32,
                                        color: AppTheme.accentRed,
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
