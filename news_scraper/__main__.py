from news_scraper.utils.csv_writer import CSVWriter


def main():
    csv_file = "data/titulares.csv"
    print("It-sWorking")
    headers = ["fecha", "medio", "titular", "url"]
    writer = CSVWriter(csv_file, headers)
    writer.write_headers()
    writer.append_data(
        {
            "fecha": "2025-07-11",
            "medio": "La Capital",
            "titulo": "Ejemplo",
            "url": "https://www.lalala.com",
        }
    )
    print(f"escrito en {csv_file}")


if __name__ == "__main__":
    main()
