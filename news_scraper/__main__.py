from news_scraper.scrapers.lacapital import LaCapitalScraper
from news_scraper.utils.csv_writer import CSVWriter
from news_scraper.utils.log_writer import LogWriter
from news_scraper.utils.constants import CSV_FILENAME, LOG_FILENAME
from news_scraper.scrapers.quedigital import QueDigitalScraper
from news_scraper.scrapers.cerodosdostres import CerodosdostresScraper


def run_scraper(scraper_class, logger, writer):
    try:
        scraper = scraper_class(logger=logger)
        logger.info(f"Iniciando scraping de {scraper.name}")
        titulares = scraper.scrape()

        if not titulares:
            logger.warning(f"No se obtuvieron titulares de {scraper.name}")
            return

        logger.info(f"Obtenidos {len(titulares)} titulares de {scraper.name}")

        for titular in titulares:
            try:
                writer.append_data(titular)
                logger.debug(f"[{scraper.name}] Escrito: {titular['titular']}")
            except Exception as e:
                logger.error(f"[{scraper.name}] Error al escribir en CSV: {e}")

    except Exception as e:
        logger.error(f"[{scraper_class.__name__}] Falló el scraping: {e}")


def main():
    log_writer = LogWriter(LOG_FILENAME)
    logger = log_writer.get_logger()

    logger.info("🚀 Inicio del scraping diario")

    headers = ["fecha", "medio", "titular", "zona_portada", "seccion", "url"]
    writer = CSVWriter(CSV_FILENAME, headers)
    writer.write_headers()

    # Lista de scrapers a ejecutar
    scrapers = [QueDigitalScraper, CerodosdostresScraper, LaCapitalScraper]

    for scraper_class in scrapers:
        run_scraper(scraper_class, logger, writer)

    logger.info("✅ Fin del scraping diario")


if __name__ == "__main__":
    main()
