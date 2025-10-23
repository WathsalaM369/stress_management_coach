# 🧘 AI-Powered Stress Management Coach

An intelligent stress management application that leverages AI (Google Gemini & OpenAI) to provide personalized stress assessment, activity recommendations, motivational support, and task scheduling to help users manage stress effectively.

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.104%2B-teal.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## 🎯 Overview

The **AI-Powered Stress Management Coach** is a comprehensive web application designed to help individuals:
- **Assess stress levels** through AI-powered questionnaires
- **Receive personalized activity recommendations** based on stress analysis
- **Get motivational support** through AI-generated messages and audio
- **Schedule and manage tasks** to reduce stress from disorganization
- **Track stress patterns** over time with database persistence
- **Access evidence-based coping strategies** tailored to individual needs

This application uses advanced AI models (Google Gemini API and OpenAI) to provide intelligent, context-aware stress management support.

---

## ✨ Features

### 🤖 AI-Powered Intelligence
- **Google Gemini AI Integration**: Advanced natural language processing for stress assessment and recommendations
- **OpenAI Support**: Alternative AI backend for enhanced flexibility
- **Multi-Agent System**: Specialized AI agents in the `agents/` directory for different tasks
- **Intelligent Analysis**: ML-based stress pattern recognition using scikit-learn

### 📊 Core Functionality
- **Stress Assessment Tool**: Comprehensive questionnaires with AI-driven analysis
- **Activity Recommendations**: Personalized suggestions based on stress levels and preferences
- **Task Scheduler**: Organize and manage daily tasks to reduce stress (`task_scheduler.html`)
- **Motivational Support**: AI-generated motivational messages with text-to-speech (`motivation_index.html`)
- **Progress Tracking**: SQLite database persistence for long-term monitoring

### 🎨 User Interface
- **Modern Web Interface**: HTML templates with responsive design
- **Interactive Dashboard**: Visual stress tracking and insights
- **Audio Support**: Text-to-speech motivational messages using gTTS
- **Real-time Updates**: Dynamic content loading and updates

### 🔧 Technical Features
- **Dual Framework Support**: Flask and FastAPI for flexible deployment
- **RESTful API**: Well-documented endpoints for integration
- **Database Management**: SQLite with SQLAlchemy ORM
- **CORS Support**: Cross-origin resource sharing enabled
- **Environment Configuration**: Secure API key management with `.env`
- **Comprehensive Testing**: pytest suite with coverage reporting

---

## 🛠 Technology Stack

### Backend Framework
- **Flask 3.0.0**: Primary web framework
- **FastAPI 0.104+**: High-performance async API alternative
- **Uvicorn**: ASGI server for FastAPI
- **Werkzeug 3.0.1**: WSGI utilities

### AI & Machine Learning
- **Google Generative AI (Gemini)**: Primary AI engine
- **OpenAI API**: Alternative AI backend
- **scikit-learn 1.3+**: Machine learning algorithms
- **NLTK 3.8+**: Natural language processing
- **NumPy 1.26+**: Numerical computing
- **Pandas 2.0+**: Data analysis and manipulation

### Database
- **SQLAlchemy 2.0+**: ORM for database operations
- **SQLite**: Lightweight database storage
  - `stress_app.db`: Main application data
  - `stress_data.db`: Stress assessment records
  - `scheduler.db`: Task scheduling data

### Utilities
- **python-dotenv**: Environment variable management
- **Pydantic 2.0+**: Data validation
- **Requests**: HTTP library
- **gTTS**: Google Text-to-Speech for audio generation
- **pygame 2.5+**: Audio playback

### Testing
- **pytest 7.0+**: Testing framework
- **pytest-cov 4.0+**: Code coverage reporting

---

## 📁 Repository Structure

```
stress_management_coach/
│
├── app.py                          # Main Flask application (97KB - primary app)
├── run_system.py                   # System launcher script
├── config.py                       # Configuration settings
├── init_db.py                      # Database initialization script
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (API keys)
│
├── agents/                         # AI Agent modules
│   └── [Specialized AI agents]
│
├── frontend/                       # Frontend assets and components
│   └── [HTML, CSS, JS files]
│
├── templates/                      # Flask HTML templates
│   ├── activity_recommendations.html
│   ├── motivation_index.html
│   ├── task_scheduler.html
│   └── [Other templates]
│
├── static/                         # Static assets (CSS, JS, images)
│   └── [Static files]
│
├── database/                       # Database files and schemas
│   ├── stress_app.db              # Main application database
│   ├── stress_data.db             # Stress tracking database
│   └── scheduler.db               # Task scheduler database
│
├── data/                           # Data files and resources
│   └── [Training data, resources]
│
├── utils/                          # Utility functions and helpers
│   └── [Helper modules]
│
├── tests/                          # Test suite
│   ├── test_api.py                # API endpoint tests
│   ├── test_llm.py                # LLM integration tests
│   ├── test_system.py             # System integration tests
│   └── .pytest_cache/             # Pytest cache
│
├── motivational_server.py          # Standalone motivation server
├── check_imports.py                # Dependency validation script
├── install_nltk_data.py            # NLTK data installer
├── 4095_requirements.txt           # Alternative requirements file
│
├── venv/                           # Virtual environment
├── __pycache__/                    # Python cache files
├── .conda/                         # Conda environment
├── .pytest_cache/                  # Pytest cache
└── .git/                           # Git repository
```

---

## 🚀 Installation

### Prerequisites

Ensure you have the following installed:
- **Python 3.12** (recommended) or Python 3.8+
- **pip** (Python package manager)
- **Git** (for cloning the repository)
- **Google Gemini API Key** (get from [Google AI Studio](https://makersuite.google.com/app/apikey))
- **OpenAI API Key** (optional, from [OpenAI Platform](https://platform.openai.com))

### Step 1: Clone the Repository

```bash
git clone https://github.com/WathsalaM369/stress_management_coach.git
cd stress_management_coach
```

### Step 2: Create Virtual Environment

**Using venv (recommended):**
```bash
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on Linux/Mac:
source venv/bin/activate
```

**Using conda:**
```bash
conda create -n stress_coach python=3.12
conda activate stress_coach
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install NLTK Data

```bash
python install_nltk_data.py
```

### Step 5: Set Up Environment Variables

Create a `.env` file in the root directory:

```env
# Google Gemini API
GEMINI_API_KEY=your_google_gemini_api_key_here

# OpenAI API (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key_here

# Database
DATABASE_URL=sqlite:///stress_app.db

# Server Configuration
HOST=127.0.0.1
PORT=5000
DEBUG=True
```

### Step 6: Initialize Database

```bash
python init_db.py
```

### Step 7: Verify Installation

```bash
python check_imports.py
```

---

## ⚙️ Configuration

### API Keys Setup

#### Google Gemini API Key:
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key to your `.env` file

#### OpenAI API Key (Optional):
1. Visit [OpenAI Platform](https://platform.openai.com)
2. Create an account or sign in
3. Navigate to API Keys section
4. Generate a new key
5. Add to `.env` file

### Database Configuration

The application uses three SQLite databases:
- **stress_app.db**: Main application data
- **stress_data.db**: Stress assessment records
- **scheduler.db**: Task scheduling data

These are automatically created when you run `init_db.py`.

---

## 💻 Usage

### Starting the Application

#### Method 1: Using the Main Application
```bash
python app.py
```

#### Method 2: Using the System Launcher
```bash
python run_system.py
```

#### Method 3: Using Flask CLI
```bash
flask run
```

#### Method 4: Using FastAPI (if configured)
```bash
uvicorn app:app --reload
```

The application will start on `http://127.0.0.1:5000` (default)

### Accessing the Application

Open your web browser and navigate to:
- **Main Dashboard**: http://localhost:5000
- **Activity Recommendations**: http://localhost:5000/activity_recommendations
- **Motivational Support**: http://localhost:5000/motivation
- **Task Scheduler**: http://localhost:5000/task_scheduler

### Using the Motivational Server (Standalone)

For standalone motivational support:
```bash
python motivational_server.py
```

---

## 🔌 API Endpoints

### Stress Assessment Endpoints

#### Submit Stress Assessment
```http
POST /api/assess
Content-Type: application/json

{
  "responses": [
    {"question_id": 1, "answer": "Often"},
    {"question_id": 2, "answer": "Sometimes"}
  ],
  "context": "Work-related stress"
}
```

**Response:**
```json
{
  "stress_level": "moderate",
  "score": 65,
  "recommendations": [...],
  "analysis": "AI-generated analysis"
}
```

### Activity Recommendations

#### Get Recommendations
```http
GET /api/recommendations?stress_level=moderate&preferences=exercise,meditation
```

**Response:**
```json
{
  "activities": [
    {
      "name": "Guided Breathing Exercise",
      "duration": "10 minutes",
      "type": "meditation",
      "difficulty": "easy"
    }
  ]
}
```

### Motivational Support

#### Get Motivational Message
```http
POST /api/motivation
Content-Type: application/json

{
  "mood": "stressed",
  "context": "work deadline"
}
```

**Response:**
```json
{
  "message": "AI-generated motivational message",
  "audio_url": "/static/audio/motivation_123.mp3"
}
```

### Task Management

#### Create Task
```http
POST /api/tasks
Content-Type: application/json

{
  "title": "Complete project report",
  "priority": "high",
  "due_date": "2025-10-25"
}
```

#### Get Tasks
```http
GET /api/tasks?status=pending&priority=high
```

---

## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# Test API endpoints
pytest tests/test_api.py

# Test LLM integration
pytest tests/test_llm.py

# Test system integration
pytest tests/test_system.py
```

### Run with Coverage Report

```bash
pytest --cov=. --cov-report=html
```

View the coverage report by opening `htmlcov/index.html` in your browser.

### Run Tests with Verbose Output

```bash
pytest -v
```

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Getting Started

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/stress_management_coach.git
   cd stress_management_coach
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/AmazingFeature
   ```
4. **Make your changes**
5. **Run tests**:
   ```bash
   pytest
   ```
6. **Commit your changes**:
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
7. **Push to the branch**:
   ```bash
   git push origin feature/AmazingFeature
   ```
8. **Open a Pull Request**

### Contribution Guidelines

- Follow PEP 8 style guide for Python code
- Write clear, descriptive commit messages
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR
- Keep pull requests focused on a single feature/fix

### Code Style

```python
# Use meaningful variable names
stress_level = calculate_stress_score(responses)

# Add docstrings to functions
def analyze_stress(data: dict) -> dict:
    """
    Analyze stress data using AI models.
    
    Args:
        data: Dictionary containing stress assessment responses
        
    Returns:
        Dictionary with analysis results and recommendations
    """
    pass

# Use type hints
def get_recommendations(stress_level: str, preferences: List[str]) -> List[dict]:
    pass
```

### Reporting Issues

Found a bug or have a feature request? Please:
1. Check if the issue already exists in [Issues](https://github.com/WathsalaM369/stress_management_coach/issues)
2. Create a new issue with:
   - Clear description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Screenshots (if applicable)
   - Environment details (Python version, OS, etc.)

---

## 👥 Contributors

Thanks to everyone who has contributed to this project!

<a href="https://github.com/WathsalaM369/stress_management_coach/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=WathsalaM369/stress_management_coach" />
</a>

### Core Team

- **Wathsala M** - *Project Lead & Developer* - [@WathsalaM369](https://github.com/WathsalaM369)

### Special Thanks

- SLIIT (Sri Lanka Institute of Information Technology) - Y3-S1 IRWA Course
- Google Gemini AI Team for the powerful AI API
- Open-source community for amazing libraries

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Wathsala M

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

## 📞 Contact

**Project Maintainer**: Wathsala M

- **GitHub**: [@WathsalaM369](https://github.com/WathsalaM369)
- **Project Link**: [https://github.com/WathsalaM369/stress_management_coach](https://github.com/WathsalaM369/stress_management_coach)
- **Institution**: SLIIT - Sri Lanka Institute of Information Technology
- **Course**: Y3-S1 IRWA (Information Retrieval and Web Analytics)

---

## 🙏 Acknowledgments

- **Google Gemini AI**: For providing powerful AI capabilities
- **OpenAI**: For alternative AI model support
- **Flask & FastAPI Communities**: For excellent web frameworks
- **SLIIT Faculty**: For guidance and support
- **Open Source Contributors**: For amazing libraries and tools

---

## 📚 Additional Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Gemini API Docs](https://ai.google.dev/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

### Research & References
- Evidence-based stress management techniques
- AI applications in mental health
- Cognitive behavioral therapy principles
- Mindfulness and meditation research

---

## 🔮 Roadmap

### Current Version (v1.0)
- ✅ AI-powered stress assessment
- ✅ Personalized activity recommendations
- ✅ Motivational support with audio
- ✅ Task scheduling system
- ✅ Database persistence
- ✅ Multi-agent AI system

### Upcoming Features (v2.0)
- [ ] Mobile application (React Native/Flutter)
- [ ] User authentication and profiles
- [ ] Social features and community support
- [ ] Integration with wearable devices
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Voice interaction capabilities
- [ ] Calendar integration
- [ ] Export reports (PDF/CSV)
- [ ] Gamification elements

### Future Considerations
- [ ] Real-time stress monitoring
- [ ] Video consultation integration
- [ ] Group therapy sessions
- [ ] Advanced ML models for prediction
- [ ] Blockchain-based health records
- [ ] AR/VR meditation experiences

---

## 🛡️ Security & Privacy

- All API keys are stored securely in `.env` file (not committed to repository)
- User data is stored locally in SQLite databases
- No personal data is shared with third parties
- CORS protection enabled
- Input validation using Pydantic
- Regular security updates for dependencies

**Note**: This application is for educational and wellness purposes. It is not a substitute for professional medical advice, diagnosis, or treatment.

---

## 🐛 Troubleshooting

### Common Issues

#### Issue: ModuleNotFoundError
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
```

#### Issue: API Key Errors
```bash
# Solution: Check .env file
# Ensure GEMINI_API_KEY is set correctly
```

#### Issue: Database Errors
```bash
# Solution: Reinitialize database
python init_db.py
```

#### Issue: NLTK Data Missing
```bash
# Solution: Install NLTK data
python install_nltk_data.py
```

#### Issue: Port Already in Use
```bash
# Solution: Change port in .env or kill existing process
# Windows: netstat -ano | findstr :5000
# Linux/Mac: lsof -ti:5000 | xargs kill
```

---

<div align="center">

**Made with love for mental wellness and stress management**

⭐ **Star this repository if you find it helpful!** ⭐

[Report Bug](https://github.com/WathsalaM369/stress_management_coach/issues) · [Request Feature](https://github.com/WathsalaM369/stress_management_coach/issues) · [Documentation](https://github.com/WathsalaM369/stress_management_coach/wiki)

---

**© 2025 Wathsala M | SLIIT Y3-S1 IRWA Project**

[⬆ Back to Top](#-ai-powered-stress-management-coach)

</div>
