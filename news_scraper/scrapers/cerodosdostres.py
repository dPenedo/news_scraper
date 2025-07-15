from news_scraper.scrapers.base import NewsScraper
from datetime import date
from bs4 import BeautifulSoup
import requests
from typing import List, Dict
from urllib.parse import urljoin


class CerodosdostresScraper(NewsScraper):
    def __init__(self, logger=None):
        super().__init__("0223", "https://www.0223.com.ar", logger)
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
        except requests.RequestException as e:
            self.log(f"Error al obtener la página: {e}", level="error")
            raise

    def _parse_generic_article(self, article_tag, zone_name: str) -> Dict:
        """Método genérico para parsear cualquier artículo"""
        try:
            title_tag = article_tag.find("h2", class_="nota__titulo-item")
            if not title_tag:
                return None

            title = title_tag.get_text(strip=True)

            # El enlace puede estar en el título o en el contenedor principal
            link_tag = (
                title_tag.parent
                if title_tag.parent.name == "a"
                else article_tag.find("a", class_="nota__media--link")
            )
            if not link_tag or not link_tag.get("href"):
                return None

            url = urljoin(self.url, link_tag["href"])

            # Extraer sección
            volanta = article_tag.find("div", class_="nota__volanta")
            seccion = (
                volanta.a.p.get_text(strip=True)
                if volanta and volanta.a and volanta.a.p
                else zone_name.rsplit("_", 1)[0]
            )

            return {
                "fecha": date.today().isoformat(),
                "medio": self.name,
                "titular": title,
                "zona_portada": zone_name,
                "seccion": seccion,
                "url": url,
            }
        except Exception as e:
            self.log(f"Error al parsear artículo: {e}", level="error")
            return None

    def _parse_section(
        self, soup: BeautifulSoup, section_name: str, section_path: str
    ) -> List[Dict]:
        """Método genérico para extraer artículos de cualquier sección"""
        articles = []

        # Buscar el contenedor de la sección
        section_container = soup.select_one(f'div.grid:has(a[href="{section_path}"])')
        if not section_container:
            self.log(f"No se encontró la sección {section_name}", level="warning")
            return articles

        # Procesar todos los artículos de la sección
        for i, article_tag in enumerate(section_container.find_all("article"), 1):
            if article_tag.find("div", class_="nota__titulo"):
                article_data = self._parse_generic_article(
                    article_tag, f"{section_name}_{i}"
                )
                if article_data:
                    articles.append(article_data)

        self.log(
            f"Se encontraron {len(articles)} artículos en sección {section_name}",
            level="info",
        )
        return articles

    def _parse_apertura_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae los artículos de la sección apertura (destacados)"""
        articles = []
        apertura_section = soup.find("div", class_="apertura")

        if not apertura_section:
            self.log("No se encontró la sección de apertura", level="warning")
            return articles

        # Artículo principal
        main_article = apertura_section.find("div", class_="nota-en-desktop")
        if main_article:
            article_tag = main_article.find("article", class_="nota--gral")
            if article_tag:
                article_data = self._parse_generic_article(
                    article_tag, "apertura_principal"
                )
                if article_data:
                    articles.append(article_data)

        # Artículos secundarios
        secondary_articles = apertura_section.find("div", class_="notas-secundarias")
        if secondary_articles:
            for i, article_tag in enumerate(
                secondary_articles.find_all("article", class_="nota--gral"), 1
            ):
                article_data = self._parse_generic_article(
                    article_tag, f"apertura_secundaria_{i}"
                )
                if article_data:
                    articles.append(article_data)

        self.log(f"Se encontraron {len(articles)} artículos en apertura", level="info")
        return articles

    def _parse_bloque_notas(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae los artículos del bloque de notas (sección inferior)"""
        articles = []
        bloque_notas = soup.find("div", class_="bloque-notas")

        if not bloque_notas:
            self.log("No se encontró el bloque de notas", level="warning")
            return articles

        for i, article_tag in enumerate(
            bloque_notas.find_all("article", class_="nota--linea"), 1
        ):
            article_data = self._parse_generic_article(article_tag, f"bloque_notas_{i}")
            if article_data:
                articles.append(article_data)

        self.log(
            f"Se encontraron {len(articles)} artículos en bloque de notas", level="info"
        )
        return articles

    # Métodos específicos para cada sección (ahora son solo wrappers del genérico)
    def _parse_mar_del_plata_section(self, soup: BeautifulSoup) -> List[Dict]:
        return self._parse_section(soup, "mar_del_plata", "/mar-del-plata")

    def _parse_argentina_section(self, soup: BeautifulSoup) -> List[Dict]:
        return self._parse_section(soup, "argentina", "/mas-alla-de-la-ciudad")

    def _parse_seguridad_section(self, soup: BeautifulSoup) -> List[Dict]:
        return self._parse_section(soup, "seguridad", "/seguridad")

    def _parse_deportes_section(self, soup: BeautifulSoup) -> List[Dict]:
        return self._parse_section(soup, "deportes", "/deportes")

    def _parse_espectaculos_section(self, soup: BeautifulSoup) -> List[Dict]:
        return self._parse_section(soup, "espectaculos", "/arte-espectaculos")

    def scrape(self) -> List[Dict]:
        """Método principal que realiza el scraping"""
        self.log("Inicio del scraping de 0223")
        titulares = []

        try:
            soup = self._get_soup(self.url)

            # Obtener artículos de apertura (destacados)
            titulares.extend(self._parse_apertura_articles(soup))

            # Obtener artículos del bloque de notas
            titulares.extend(self._parse_bloque_notas(soup))

            # Obtener artículos de secciones específicas
            titulares.extend(self._parse_mar_del_plata_section(soup))
            titulares.extend(self._parse_argentina_section(soup))
            titulares.extend(self._parse_seguridad_section(soup))
            titulares.extend(self._parse_deportes_section(soup))
            titulares.extend(self._parse_espectaculos_section(soup))

            self.log(f"Total de titulares encontrados: {len(titulares)}")

        except Exception as e:
            self.log(f"Error durante el scraping: {e}", level="error")
            raise

        self.log("Fin del scraping")
        return titulares
