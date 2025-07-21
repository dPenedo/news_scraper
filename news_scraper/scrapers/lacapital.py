from typing import List, Dict

import requests

from news_scraper.scrapers.base import NewsScraper
from bs4 import BeautifulSoup


class LaCapitalScraper(NewsScraper):

    def __init__(self, logger=None):
        super().__init__("La capital", "https://www.lacapitalmdp.com/", logger)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def _get_soup(self, url: str) -> BeautifulSoup:
        """Obtiene el contenido HTML y lo parsea con BeautifulSoup"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests as e:
            self.log(f"Error al obtener la página: {e}", level="error")
            raise

    def scrape(self) -> List[Dict]:
        """Método principal que realiza el scraping"""
        self.log("Inicio del scraping de La capital")
        titulares = []

        try:
            soup = self._get_soup(self.url)

            # # Obtener artículos de apertura (destacados)
            # titulares.extend(self._parse_apertura_articles(soup))
            #
            # # Obtener artículos del bloque de notas
            # titulares.extend(self._parse_bloque_notas(soup))
            #
            # # Obtener artículos de secciones específicas
            # titulares.extend(self._parse_mar_del_plata_section(soup))
            # titulares.extend(self._parse_argentina_section(soup))
            # titulares.extend(self._parse_seguridad_section(soup))
            # titulares.extend(self._parse_deportes_section(soup))
            # titulares.extend(self._parse_espectaculos_section(soup))

            self.log(f"Total de titulares encontrados: {len(titulares)}")

        except Exception as e:
            self.log(f"Error durante el scraping: {e}", level="error")
            raise

        self.log("Fin del scraping")
        return titulares
