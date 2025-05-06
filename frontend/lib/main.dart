import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_selector/file_selector.dart';

void main() {
  runApp(MaterialApp(
    home: ImageToArduinoApp(),
    debugShowCheckedModeBanner: false,
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

  void _uploadImageToArduino() {
    if (_selectedImage != null) {
      // TODO: Add Arduino communication logic here
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Image is being sent to the Arduino..."),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Send Image to Arduino'),
        centerTitle: true,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ElevatedButton.icon(
                onPressed: _chooseImage,
                icon: Icon(Icons.image),
                label: Text('Pick an Image'),
                style: ElevatedButton.styleFrom(minimumSize: Size.fromHeight(50)),
              ),
              SizedBox(height: 30),
              _selectedImage != null
                  ? Column(
                children: [
                  Image.file(_selectedImage!, height: 200),
                  SizedBox(height: 10),
                  Text(
                    'Image selected successfully!',
                    style: TextStyle(color: Colors.green),
                  ),
                ],
              )
                  : Text(
                'No image selected yet.',
                style: TextStyle(color: Colors.grey),
              ),
              SizedBox(height: 30),
              ElevatedButton.icon(
                onPressed: _selectedImage != null ? _uploadImageToArduino : null,
                icon: Icon(Icons.send),
                label: Text('Send to Arduino'),
                style: ElevatedButton.styleFrom(
                  minimumSize: Size.fromHeight(50),
                  backgroundColor: _selectedImage != null ? Colors.blue : Colors.grey,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
