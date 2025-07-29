# News Scraper

This project scrapes **news headlines** from local newspapers in Mar del Plata (Argentina) and stores the results in a CSV file.

---

## ⚙️ Requirements

Before you start, make sure you have the following installed:

- [Python 3.10 or later](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)

--

## 🚀 Installation

### Clone the repository

Open a terminal and run:

```
git clone https://github.com/dPenedo/news_scraper.git
cd news_scraper
```

### Create a virtual environment

Inside the project folder:

```
python -m venv env
```

Activate the virtual environment:

- Linux/macOS:

```sh
source env/bin/activate
```

- CMD:

```
env\Scripts\activate.bat
```

- PowerShell:

```
env\Scripts\Activate.ps1
```

You should now see `(env)` at the beginning of the terminal prompt.

---

## 📦 Install dependencies

With the virtual environment active, run:

```
pip install -r requirements.txt
```

---

## ▶️ Usage

With the environment activated, run:

```
python -m news_scraper
```

The results will be saved as a `.csv` file in the project folder.

---

## 📄 CSV Format

Each row represents a news article. The columns are:

- **Date**
- **Source** (lacapitalmdp, 0223, quedigital)
- **Headline**
- **Front page zone** (depends on how the media outlet labels it)
- **Section** (varies by outlet):
  - QueDigital: uses traditional sections (society, culture, sports…)
  - 0223: uses loose tags (e.g., Robbery, Violence, Attempted Femicide, Weather)
- **URL**

---

## 🧱 Project Structure and Features

- Uses `requests` and `BeautifulSoup` for HTML parsing.
- Logs events such as collected headlines, errors, and timestamps using Python’s built-in `logging` module.
- Written in Python using an **object-oriented structure** with custom classes for scraping and data handling.
- Modular design makes it easy to extend or adapt for other sources.

---

## 🛡️ Disclaimer

This project was developed for academic purposes by a research group based in Mar del Plata. The script collects publicly available news metadata (titles, URLs, tags) and **does not store or redistribute full article content**.

This code is not intended for commercial use. Always respect the [terms of service](https://www.lacapitalmdp.com/terminos-y-condiciones/) of the websites you interact with.

If you use this code, ensure your use complies with applicable laws and the policies of the media outlets.

---

## 🌎 About the Project

This scraper is part of a broader sociological study analyzing media coverage patterns in local news. It runs daily as an [AWS Lambda](https://aws.amazon.com/lambda/) function and stores results in an [S3 bucket](https://aws.amazon.com/s3/).
