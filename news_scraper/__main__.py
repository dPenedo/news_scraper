from news_scraper.utils.csv_writer import CSVWriter
from news_scraper.utils.log_writer import LogWriter
from news_scraper.utils.constants import CSV_FILENAME, LOG_FILENAME
from news_scraper.scrapers.quedigital import QueDigitalScraper


def main():
    log_writer = LogWriter(LOG_FILENAME)
    logger = log_writer.get_logger()

    logger.info("Inicio del scraping diario")

    headers = ["fecha", "medio", "titular", "zona_portada", "seccion", "url"]

    writer = CSVWriter(CSV_FILENAME, headers)

    try:
        writer.write_headers()

        quedigital_scraper = QueDigitalScraper(logger=logger)

        logger.info("Iniciando scraping de QueDigital")
        titulares = quedigital_scraper.scrape()

        if not titulares:
            logger.warning("No se obtuvieron titulares de QueDigital")
        else:
            logger.info(f"Obtenidos {len(titulares)} titulares de QueDigital")

            for titular in titulares:
                try:
                    writer.append_data(titular)
                    logger.debug(f"Escrito titular: {titular['titular']}")
                except Exception as e:
                    logger.error(f"Error al escribir titular en CSV: {e}")
                    continue

            logger.info(f"Titulares escritos en {CSV_FILENAME}")

    except Exception as e:
        logger.error(f"Error general en el proceso de scraping: {e}")
        raise

    logger.info("Fin del scraping diario")


if __name__ == "__main__":
    main()
