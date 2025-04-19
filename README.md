# KudSight <img src="app/static/favicon.ico" alt="KudSight Favicon" width="32">


 **This app is experimental and has not fully tested !**
</br>


**KudSight** is an experimental, Python-based static analysis tool that helps developers explore class relationships in source code using interactive 3D and UML-style diagrams — all directly in the browser.

> 🔍 Supports **Java** and **C++** as primary languages, with early support for **C#** and **Kotlin**.


## 🚀 v0.6.0-beta Highlights (April 19, 2025)

-  Enhanced support for **Java** and **C++**
-  Toggle between **3D Graph** and **UML-style** diagram rendering
-  **Dark/Light mode switching**
-  **Auto-refresh** analysis results
-  **Selective class rendering**
-  Export diagrams as **PNG** or **PlantUML (.puml)**
-  Improved UI and CSS
-  Updated Docker image for easy deployment


## 🔧 Core Features

| Category | Description |
|----------|-------------|
|  Language Support | - Java (primary)<br>- C++ (stable)<br>- C# and Kotlin (experimental) |
|  Code Analysis | - Extracts Inheritance, Implementation, and Dependency relations<br>- Supports package/module groupings |
|  Visualization | - 3D Graph rendering (with camera controls)<br>- UML-style layout toggle<br>- Selective node rendering |
|  UI & UX | - Sidebar filtering by Category and Items<br>- Node focus, reset, zoom/pan controls<br>- Dark/Light theme toggle |
|  Export | - PNG and PlantUML output<br>- Screenshot functionality<br>- Node position/layout persistence |
|  Tooling | - Web-based UI and CLI options<br>- Dockerized for easy, cross-platform use |



**Note**
There are two ways to use this app. The first one is installing all the packages and running the app. And the second one is using docker.
I recommend using docker for sake of convenience and avoiding any conflict in installing the packages. So if you want to use docker you can jump to that section.
</br>

## Setting up manually
### Installation

> **Quick Start:** Run the setup script:
```bash
./setup.sh
```

#### Manual Setup

1. **Clone the repo with submodules**:

```bash
git clone --recurse-submodules https://github.com/Heydarchi/KudSight.git
cd KudSight
```

2. **Install Python and dependencies**:

```bash
sudo apt install python3 python-is-python3 python3-venv default-jre graphviz -y
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```


### Usage

#### Web Server (Recommended)

```bash
python app.py
```

Then open in your browser:

```
http://127.0.0.1:5000/
```

#### Command Line

```bash
python FileAnalyzer.py test/test_files/java
```

Results are saved to:

```
app/static/out/
```

</br>

## Docker


### Pull the Docker Image from DockerHub and Run

I have provide a docker image including the latest version of the application that you can easily pull and run it without setting up anything on you PC.

*Notes:*
- Create an out folder in the directory you want to run the docker to store the analysis result. (Mandatory)
- You can mount other folder, drivers and disks if you like. But the first part "$PWD/out:/app/static/out" should be kept.

Pull the image:
```bash
docker pull mhheydarchi/kudsight:latest
```

Run it:
```bash
docker run -it --rm --network host -v "$PWD/out:/app/static/out" -v "$HOME:/home/$USER" -v "/media:/media" -p 5000:5000  mhheydarchi/kudsight:latest
```

Now visit: [http://localhost:5000](http://localhost:5000)

</br>

### Build the Docker Image locally and Run it

if you're interested to build the docker image locally and use it you can follow these steps:

### Build the Docker Image

```bash
docker build -t kudsight .
```

#### Run KudSight in Docker

> Create an out folder in the directory you want to run the docker to store the analysis result. (Mandatory)
> You can mount other folder, drivers and disks if you like. But the first part "$PWD/out:/app/static/out" should be kept.

```bash
docker run -it --rm --network host -v "$PWD/out:/app/static/out" -v "$HOME:/home/$USER" -v "/media:/media" -p 5000:5000  kudsight
```


Now visit: [http://localhost:5000](http://localhost:5000)

</br>

## 🤝 Contributing

We ❤️ contributions! Whether it's code, bug reports, or docs — you're welcome.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.


## 🚧 Roadmap

Check [TODO.md](TODO.md) for upcoming features and known issues. Your input is appreciated.


## 🪪 License

Licensed under the **Apache License 2.0**.


## 📢 Contact

Have ideas, feedback, or bugs to report? Open an [issue](https://github.com/Heydarchi/KudSight/issues) or start a discussion on GitHub!
