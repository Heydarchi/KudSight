# ClassRelExposer
The aim of this python project is to find and exposing the class relationship

### The supported languages are:
- C++
- Java 
- CSharp (C#)
- Kotlin

<br/>

The code is tested for Java but not that much for C++ and C-Sharp. Of course, it is not completed yet and has some flaws and issues in processing. Very welcome to report or any kind of contribution.

Feel free to create a ticket or send me a message/report.

<br/>

### PlantUml

Generating the PNG files is based on [PlantUml](http://www.plantuml.com) that I put a jar version in this project.


## Installation
#### Note : The 1st & 2nd steps can be skipped by running the `setup.sh` script.
```
./setup.sh
```
&ensp;

1. Clone the project and its submodule (Leav it if you have already cloned the repo!):

```
git clone https://github.com/Heydarchi/ClassRelExposer.git
```
&ensp;

2. Inside the cloned folder, run the following command to update the submodule:

```
git submodule update --init --recursive
```

1. Install Python 3.8 or a newer version, PythonIsPython3:

```
sudo apt install python3 python-is-python3  python3-venv -y
```
&ensp;

4. Create & Activate Virtual Environment 

```
python3 -m venv venv
source venv/bin/activate
```
&ensp;

5. Install python packages

```
pip install -r requirements.txt
```
&ensp;


<br/>

## **How to run**

#### **To run Web server** 

```
python app.py
```


<br/>
>Open the below url in a browser

```
http://127.0.0.1:5000/
```

#### **To run sample from command line** 

```
python FileAnalyzer.py test/test_files/java
```

>The result can be found in the **out** folder

<br/>

## Docker


### Build Docker

```
docker build -t kudsight .
```

### Run by Docker

```
docker run -it --network host  --rm   -v "$PWD/app/static/out:/app/static/out"   -v "$HOME/Projects/code:/mnt/code"   -p 5000:5000   kudsight
```


## Contributing

Thank you for your interest in contributing to SELinux Explorer! We welcome and appreciate any contributions, whether it's bug reports, feature requests, code, documentation, or testing. Please refer to our [CONTRIBUTION.md](CONTRIBUTING.md) file for detailed guidelines on how to set up your development environment, check code style, run tests, and submit your changes.

## Features and TODOs

This project is under active development, and we're continuously working on improving and expanding its functionality. For a detailed list of features and tasks that we're planning to implement, please refer to the [TODO List](TODO.md) file. We welcome your contributions and feedback, so feel free


