# KudSight

**KudSight** is a Python-based static analysis tool that helps visualize **class relationships** in source code across several programming languages.

It supports extracting inheritance, implementation, and composition relations, and can render UML-style diagrams in browser..


## ✨ Features

- Language Support: Java, C++, C#, Kotlin
- Class relationship extraction: inheritance, implementation, dependencies
- Diagram generation with PlantUML
- Web-based UI and CLI
- Dockerized for cross-platform use


## 🧪 Supported Languages

- ✅ Java (primary support)
- ⚠️ C++ (partial support)
- ⚠️ C# (partial support)
- ⚠️ Kotlin (experimental)

> Java, C++ and C# support is most stable. Other languages are work-in-progress. Contributions welcome!


## 🚀 Installation

> **Quick Start:** Run the setup script:
```bash
./setup.sh
```

### 🔧 Manual Setup

1. **Clone the repo with submodules**:

```bash
git clone --recurse-submodules https://github.com/Heydarchi/KudSight.git
cd KudSight
```

2. **Install Python and dependencies**:

```bash
sudo apt install python3 python-is-python3 python3-venv -y
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```


## 📊 Usage

### 🌐 Web Server (Recommended)

```bash
python app.py
```

Then open in your browser:

```
http://127.0.0.1:5000/
```

### 🧪 Command Line

```bash
python FileAnalyzer.py test/test_files/java
```

Results are saved to:

```
app/static/out/
```


## 🐳 Docker Support

### 🔨 Build the Docker Image

```bash
docker build -t kudsight .
```

### ▶️ Run KudSight in Docker

```bash
docker run -it --rm --network host \
  -v "$PWD/app/static/out:/app/static/out" \
  -v "$HOME/Projects/code:/mnt/code" \
  -p 5000:5000 \
  kudsight
```

Now visit: [http://localhost:5000](http://localhost:5000)


## 🖼️ PlantUML Integration

UML diagrams are generated using a bundled [PlantUML JAR](https://plantuml.com/download). No external setup is required.


## 🤝 Contributing

We ❤️ contributions! Whether it's code, bug reports, or docs — you're welcome.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.


## 🚧 Roadmap

Check [TODO.md](TODO.md) for upcoming features and known issues. Your input is appreciated.


## 🪪 License

Licensed under the **Apache License 2.0**.


## 📢 Contact

Have ideas, feedback, or bugs to report? Open an [issue](https://github.com/Heydarchi/KudSight/issues) or start a discussion on GitHub!
