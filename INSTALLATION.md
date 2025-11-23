# Farm IQ AI Agro - Installation Guide

This guide provides step-by-step instructions for installing and setting up the Farm IQ AI Agro application.

## Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd farm-iq-ai-agro-main
```

### 2. Choose Your Installation Type

#### Option A: Minimal Installation (Recommended for Development)
```bash
cd server
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install minimal requirements
pip install -r requirements-minimal.txt
```

#### Option B: Complete Installation (All Features)
```bash
cd server
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install all requirements
pip install -r requirements.txt
```

#### Option C: Development Installation (With Dev Tools)
```bash
cd server
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install development requirements
pip install -r requirements-dev.txt
```

#### Option D: Production Installation (Optimized)
```bash
cd server
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install production requirements
pip install -r requirements-prod.txt
```

## Requirements Files Explained

### 1. `requirements.txt` - Complete Requirements
- **Purpose**: Full installation with all features
- **Use Case**: When you want all functionality including optional features
- **Size**: ~2GB (includes ML libraries)
- **Includes**: All core dependencies + optional features

### 2. `requirements-minimal.txt` - Essential Only
- **Purpose**: Core functionality only
- **Use Case**: Quick setup, development, or resource-constrained environments
- **Size**: ~500MB
- **Includes**: Only essential dependencies for basic functionality

### 3. `requirements-dev.txt` - Development Tools
- **Purpose**: Development environment with testing and debugging tools
- **Use Case**: When developing or contributing to the project
- **Size**: ~3GB
- **Includes**: All production requirements + development tools

### 4. `requirements-prod.txt` - Production Optimized
- **Purpose**: Production deployment with performance optimizations
- **Use Case**: Server deployment, production environments
- **Size**: ~2.5GB
- **Includes**: Production-optimized versions + monitoring tools

## Installation Steps by Environment

### Development Environment

1. **Install Python 3.9+**
   ```bash
   # Check Python version
   python --version
   ```

2. **Create Virtual Environment**
   ```bash
   cd server
   python -m venv venv
   ```

3. **Activate Virtual Environment**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

4. **Install Dependencies**
   ```bash
   # For development
   pip install -r requirements-dev.txt
   
   # Or for minimal setup
   pip install -r requirements-minimal.txt
   ```

5. **Set Up Environment Variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

6. **Initialize Database**
   ```bash
   alembic upgrade head
   ```

7. **Run the Application**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Production Environment

1. **Install System Dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install python3.9 python3.9-venv python3-pip postgresql-client
   
   # CentOS/RHEL
   sudo yum install python39 python39-pip postgresql
   ```

2. **Create Application User**
   ```bash
   sudo useradd -m -s /bin/bash farmiq
   sudo su - farmiq
   ```

3. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd farm-iq-ai-agro-main/server
   python3.9 -m venv venv
   source venv/bin/activate
   pip install -r requirements-prod.txt
   ```

4. **Configure Environment**
   ```bash
   cp env.example .env
   # Edit .env with production values
   ```

5. **Setup Database**
   ```bash
   # For PostgreSQL
   createdb farmiq
   alembic upgrade head
   ```

6. **Run with Gunicorn**
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

### Docker Installation

1. **Using Docker Compose (Recommended)**
   ```bash
   # From project root
   docker-compose up --build
   ```

2. **Using Dockerfile**
   ```bash
   cd server
   docker build -t farmiq-backend .
   docker run -p 8000:8000 farmiq-backend
   ```

## Frontend Installation

1. **Install Node.js 18+**
   ```bash
   # Check Node version
   node --version
   npm --version
   ```

2. **Install Dependencies**
   ```bash
   # From project root
   npm install
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```

4. **Build for Production**
   ```bash
   npm run build
   ```

## Verification

### Backend Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "FarmIQ Backend is running"
}
```

### Frontend Access
- Open browser to `http://localhost:5173`
- Should see the Farm IQ application

## Troubleshooting

### Common Issues

1. **Python Version Error**
   ```bash
   # Ensure Python 3.9+
   python --version
   # If not, install correct version
   ```

2. **Virtual Environment Issues**
   ```bash
   # Delete and recreate
   rm -rf venv
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

3. **Permission Errors**
   ```bash
   # Fix permissions
   chmod +x venv/bin/activate
   ```

4. **Port Already in Use**
   ```bash
   # Kill process using port 8000
   lsof -ti:8000 | xargs kill -9
   # Or use different port
   uvicorn main:app --port 8001
   ```

5. **Model Loading Errors**
   ```bash
   # Ensure model files are in server/models/
   ls server/models/
   # Should show: plant_disease_model_1_latest.pt, disease_info.csv, supplement_info.csv
   ```

### Dependencies Issues

1. **PyTorch Installation**
   ```bash
   # For CPU only
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   
   # For GPU (CUDA)
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

2. **Pillow Installation Issues**
   ```bash
   # Install system dependencies first
   # Ubuntu/Debian
   sudo apt-get install libjpeg-dev zlib1g-dev
   
   # Then install Pillow
   pip install --upgrade pillow
   ```

## Performance Optimization

### For Development
- Use `requirements-minimal.txt` for faster installation
- Enable auto-reload: `uvicorn main:app --reload`

### For Production
- Use `requirements-prod.txt` for optimized performance
- Use Gunicorn with multiple workers
- Enable Redis for caching
- Use PostgreSQL instead of SQLite

## Next Steps

After successful installation:

1. **Configure API Keys** in `.env` file
2. **Upload Model Files** to `server/models/`
3. **Run Database Migrations**: `alembic upgrade head`
4. **Start Backend**: `uvicorn main:app --host 0.0.0.0 --port 8000`
5. **Start Frontend**: `npm run dev`
6. **Access Application**: Open `http://localhost:5173`

## Support

For installation issues:
1. Check the troubleshooting section above
2. Verify all system requirements are met
3. Check the logs for specific error messages
4. Contact the development team for assistance
