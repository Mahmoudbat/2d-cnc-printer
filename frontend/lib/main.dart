import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_selector/file_selector.dart';

const String imageStoragePath = "../Temp/input";

void main() {
  runApp(MaterialApp(
    home: ImageToArduinoApp(),
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: Color(0xFF1E1E1E),
      colorScheme: ColorScheme.fromSeed(
        seedColor: Color(0xFF00BCD4), // Cyan-blue
        brightness: Brightness.dark,
      ),
      textTheme: TextTheme(
        bodyMedium: TextStyle(
          fontSize: 16,
          color: Color(0xFFE0E0E0), // Light gray text
        ),
        titleLarge: TextStyle(
          fontWeight: FontWeight.bold,
          color: Color(0xFFE0E0E0),
        ),
      ),
    ),
  ));
}

class ImageToArduinoApp extends StatefulWidget {
  @override
  _ImageToArduinoAppState createState() => _ImageToArduinoAppState();
}

class _ImageToArduinoAppState extends State<ImageToArduinoApp> {
  File? _selectedImage;

  Future<void> _chooseImage() async {
    const XTypeGroup typeGroup = XTypeGroup(
      label: 'images',
      extensions: ['jpg', 'jpeg', 'png'],
    );
    final XFile? file = await openFile(acceptedTypeGroups: [typeGroup]);

    if (file != null) {
      setState(() {
        _selectedImage = File(file.path);
      });
    }
  }

  Future<void> _uploadImageToArduino() async {
    if (_selectedImage != null) {
      final fileExtension = _selectedImage!.path.split('.').last;
      final savedImage = File('$imageStoragePath.$fileExtension');
      await _selectedImage!.copy(savedImage.path);

      final shellCommand = '''
        cd ../backend && \\
        source .venv/bin/activate && \\
        python tosvg.py && \\
        python togcode.py && \\
        python Serial-comm.py
      ''';

      try {
        final result = await Process.run('bash', ['-c', shellCommand]);

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              result.exitCode == 0
                  ? "Image processed and sent successfully."
                  : "Error: ${result.stderr}",
              style: TextStyle(color: Colors.black),
            ),
            duration: Duration(seconds: 3),
            backgroundColor: result.exitCode == 0
                ? Colors.greenAccent[400]
                : Colors.red[300],
          ),
        );
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              "Execution failed: $e",
              style: TextStyle(color: Colors.black),
            ),
            duration: Duration(seconds: 3),
            backgroundColor: Colors.red[300],
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isImageSelected = _selectedImage != null;

    return Scaffold(
      appBar: AppBar(
        title: Text('Send Image to Arduino'),
        centerTitle: true,
        elevation: 0,
        backgroundColor: Color(0xFF121212),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              FilledButton.icon(
                onPressed: _chooseImage,
                icon: Icon(Icons.image_outlined, color: Colors.black),
                label: Text('Pick an Image', style: TextStyle(color: Colors.black)),
                style: FilledButton.styleFrom(
                  backgroundColor: Color(0xFF00BCD4),
                  minimumSize: Size.fromHeight(50),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
              SizedBox(height: 30),
              if (isImageSelected) ...[
                ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Image.file(_selectedImage!, height: 200),
                ),
                SizedBox(height: 10),
                Text(
                  'Image selected successfully!',
                  style: TextStyle(color: Colors.greenAccent[400]),
                ),
              ] else
                Text(
                  'No image selected yet.',
                  style: TextStyle(color: Colors.grey[500]),
                ),
              SizedBox(height: 30),
              FilledButton.icon(
                onPressed: isImageSelected ? _uploadImageToArduino : null,
                icon: Icon(Icons.send, color: Colors.black),
                label: Text('Send to Arduino', style: TextStyle(color: Colors.black)),
                style: FilledButton.styleFrom(
                  backgroundColor: isImageSelected
                      ? Color(0xFF00BCD4)
                      : Color(0xFF00BCD4).withOpacity(0.3),
                  minimumSize: Size.fromHeight(50),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
