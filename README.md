# DeepGuard - Deepfake Detection System

A comprehensive web-based deepfake detection system that analyzes video files using multiple AI detection methods and provides detailed reports with visual insights.

## 🚀 Features

- **Multi-Algorithm Detection**: Uses CNN, LSTM, and Transformer-based detection methods
- **Web Interface**: User-friendly Flask web application
- **User Management**: Secure authentication with admin capabilities
- **Visual Reports**: Generate PDF reports with charts and frame analysis
- **History Tracking**: Keep track of all analysis results
- **Frame Analysis**: Extract and analyze key frames from videos
- **Real-time Processing**: Upload and analyze videos with progress feedback

## 📋 Requirements

### System Requirements
- Python 3.7 or higher
- 2GB+ RAM recommended
- 1GB+ free disk space

### Python Dependencies
```
Flask==2.3.3
Werkzeug==2.3.7
opencv-python==4.8.1.78
numpy==1.24.3
matplotlib==3.7.2
reportlab==4.0.4
Pillow==10.0.1
```

## 🛠 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/deepguard-detection-system.git
cd deepguard-detection-system
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create Required Directories
The application will automatically create necessary directories, but you can create them manually:
```bash
mkdir uploads
mkdir uploads/frames
mkdir templates
mkdir static
```

## 🚀 Usage

### Starting the Application
```bash
python app.py
```

The application will start on `http://localhost:5000`

### Default Login Credentials
- **Admin Account**: 
  - Username: `admin`
  - Password: `admin123`
- **Test Account**: 
  - Username: `test`
  - Password: `test123`

⚠️ **Important**: Change these default passwords immediately in production!

### Supported Video Formats
- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- Maximum file size: 100MB

## 📁 Project Structure

```
deepguard-detection-system/
│
├── app.py                 # Main Flask application
├── models.py             # User management and data storage
├── processing.py         # Video processing and AI detection
├── report_utils.py       # PDF report generation
├── requirements.txt      # Python dependencies
├── README.md            # This file
│
├── templates/           # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── home.html
│   ├── detect.html
│   ├── report.html
│   └── ...
│
├── static/             # CSS, JS, and static assets
│   ├── css/
│   ├── js/
│   └── images/
│
└── uploads/            # File upload directory (created automatically)
    └── frames/         # Extracted frame storage
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key-here
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=104857600
DEBUG=False
```

### Security Configuration
For production deployment:
1. Change the `SECRET_KEY` in `app.py`
2. Set `SESSION_COOKIE_SECURE = True` for HTTPS
3. Update default admin credentials
4. Configure proper file permissions

## 🎯 How It Works

### Detection Pipeline
1. **Video Upload**: User uploads a video file through the web interface
2. **Frame Extraction**: System extracts key frames from the video
3. **Multi-Algorithm Analysis**:
   - **CNN Detector**: Analyzes spatial features and artifacts
   - **LSTM Detector**: Examines temporal inconsistencies
   - **Transformer Detector**: Evaluates global context patterns
4. **Score Fusion**: Combines results using weighted averaging
5. **Report Generation**: Creates detailed PDF reports with visualizations

### Detection Methods
- **CNN (Convolutional Neural Network)**: Focuses on spatial artifacts and image inconsistencies
- **LSTM (Long Short-Term Memory)**: Analyzes temporal patterns across frames
- **Transformer**: Evaluates global contextual relationships

*Note: Current implementation uses simulated detectors for demonstration. In production, these would be replaced with fully trained deep learning models.*

## 📊 Features Overview

### User Features
- **Video Analysis**: Upload and analyze videos for deepfake detection
- **Results History**: View all previous analysis results
- **PDF Reports**: Download detailed reports with charts and insights
- **Account Management**: Update passwords and manage profile

### Admin Features
- **User Management**: Create, delete, and manage user accounts
- **System Overview**: View all user activities and results
- **Password Reset**: Reset user passwords when needed

## 🔒 Security Features

- Secure password hashing using Werkzeug
- Session-based authentication
- File upload validation and sanitization
- Directory traversal protection
- Admin-only access controls
- Security headers implementation

## 🚨 Limitations & Disclaimers

1. **Prototype System**: This is a demonstration system with simulated AI detectors
2. **Educational Purpose**: Designed for learning and research, not production use
3. **Accuracy**: Detection accuracy depends on training data and model quality
4. **File Size**: Limited to 100MB video files
5. **Processing Time**: Analysis time varies based on video length and system resources

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🛠 Development Setup

### For Developers
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run with debug mode
export FLASK_ENV=development
python app.py
```

### Testing
```bash
# Run unit tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=. tests/
```

## 📞 Support

For support, please open an issue on GitHub or contact the development team.

## 🔮 Future Enhancements

- [ ] Integration with real AI models (TensorFlow/PyTorch)
- [ ] Support for additional video formats
- [ ] Real-time video stream analysis
- [ ] Mobile app development
- [ ] API endpoints for third-party integration
- [ ] Advanced visualization dashboard
- [ ] Batch processing capabilities

## 🙏 Acknowledgments

- OpenCV for video processing capabilities
- Flask framework for web application structure
- ReportLab for PDF generation
- Matplotlib for chart visualization

---

**⚠️ Important Security Notice**: This system is for educational and research purposes. Always ensure proper security measures when deploying in production environments.
