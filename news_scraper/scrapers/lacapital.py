import logging
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
import requests

from news_scraper.scrapers.base import NewsScraper


class LaCapitalScraper(NewsScraper):

    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__(
            name="La capital",
            url="https://www.lacapitalmdp.com/",
            logger=logger,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        )

    def _get_soup(self, url: str) -> BeautifulSoup:
        """Obtiene el contenido HTML y lo parsea con BeautifulSoup"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            self.log(f"Error al obtener la página: {e}", level="error")
            raise

    def _extract_section_from_url(self, url: str) -> str:
        """Extrae la categoría temática de la URL del artículo"""
        try:
            path = url.replace(self.url, "").strip("/")
            parts = path.split("/")

            section_map = {
                "policiales": "Policiales",
                "la-ciudad": "La Ciudad",
                "el-pais": "El País",
                "el-mundo": "El Mundo",
                "interes-general": "Interés General",
                "temas": "Especiales",
                "cotizaciones": "Economía",
            }

            if parts and parts[0] in section_map:
                return section_map[parts[0]]
            return parts[0].replace("-", " ").title() if parts else "General"
        except Exception as e:
            self.log(f"Error al extraer categoría de {url}: {e}", level="warning")
            return "General"

    def _get_section_title(self, section: Tag) -> str:
        """Extrae el título de una sección si está disponible"""
        title_tag = section.find("div", class_="section__title")
        if not title_tag:
            return ""

        h3_tag = title_tag.find("h3")
        if not h3_tag:
            return ""

        return self.clean_text(h3_tag.get_text(strip=True))

    def _parse_principal_section(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extrae los artículos de la sección principal"""
        articles = []
        section = soup.find("section", class_="section--first")

        if not section:
            self.log("No se encontró la sección principal", level="warning")
            return articles

        # Artículo principal
        main_article = (
            section.find("div", class_="col-sm-8").find("article")
            if section.find("div", class_="col-sm-8")
            else None
        )
        if main_article:
            data = self._extract_article_data(main_article, "Principal - Destacado")
            if data:
                articles.append(data)

        # Artículos secundarios
        secondary_articles = (
            section.find("div", class_="principal_2").find_all("article")
            if section.find("div", class_="principal_2")
            else []
        )
        for i, article in enumerate(secondary_articles, 1):
            data = self._extract_article_data(article, f"Principal - Secundario {i}")
            if data:
                articles.append(data)

        self.log(
            f"Se encontraron {len(articles)} artículos en la sección principal",
            level="info",
        )
        return articles

    def _parse_regular_sections(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extrae los artículos de las secciones regulares con detección de títulos"""
        articles = []
        sections = soup.find_all("section", class_="regular-notas")

        if not sections:
            self.log("No se encontraron secciones regulares", level="warning")
            return articles

        for i, section in enumerate(sections, 1):
            section_title = self._get_section_title(section)
            zone_name = f"Sección Regular {i}" + (
                f" - {section_title}" if section_title else ""
            )

            section_articles = section.find_all("article", class_="nota")
            for article in section_articles:
                data = self._extract_article_data(article, zone_name)
                if data:
                    articles.append(data)

            self.log(
                f"Se encontraron {len(section_articles)} artículos en {zone_name}",
                level="info",
            )

        return articles

    def _parse_ranking_section(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extrae los artículos de lo más visto"""
        articles = []

        # Buscamos el contenedor principal de la sección
        ranking_container = soup.find("div", class_="post_ranking")

        if not ranking_container:
            self.log("No se encontró la sección de lo más visto", level="warning")
            return articles

        # Extraemos el título de la sección
        section_title_tag = soup.find(
            "h3",
            string=lambda text: "lo más visto hoy" in text.lower() if text else False,
        )
        section_title = (
            self.clean_text(section_title_tag.get_text(strip=True))
            if section_title_tag
            else "Lo más visto"
        )

        # Buscamos todos los elementos de la lista
        list_items = ranking_container.find_all("li")

        for item in list_items:
            try:
                link = item.find("a")
                if not link or not link.get("href"):
                    continue

                url = urljoin(self.url, link["href"])
                title = self.clean_text(link.get_text(strip=True))

                # Eliminamos el número del título (ej: "1matan a un..." -> "matan a un...")
                title = " ".join(title.split()[1:]) if title.split() else title

                articles.append(
                    {
                        "fecha": self.get_current_date(),
                        "medio": self.name,
                        "titular": title,
                        "zona_portada": f"Ranking - {section_title}",
                        "seccion": self._extract_section_from_url(url),
                        "url": url,
                    }
                )

            except Exception as e:
                self.log(f"Error al procesar artículo del ranking: {e}", level="error")
                continue

        self.log(
            f"Se encontraron {len(articles)} artículos en {section_title}", level="info"
        )
        return articles

    def _parse_canal2_section(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extrae los titulares de Canal 2"""
        articles = []

        # Buscamos el contenedor principal de la sección Canal 2
        canal2_section = soup.find("h3", string="Canal 2").find_parent(
            "div", class_="col-12"
        )

        if not canal2_section:
            self.log("No se encontró la sección de Canal 2", level="warning")
            return articles

        # Buscamos todos los items de Canal 2
        canal2_items = canal2_section.find_all(
            "div", class_=["col-xs-6", "col-sm-6", "col-md-6", "col-lg-6"]
        )

        for item in canal2_items:
            try:
                link = item.find("a")
                if not link or not link.get("href"):
                    continue

                url = link["href"]
                title = (
                    self.clean_text(item.find("p").get_text(strip=True))
                    if item.find("p")
                    else ""
                )

                articles.append(
                    {
                        "fecha": self.get_current_date(),
                        "medio": "Canal 2",  # Especificamos que viene de Canal 2
                        "titular": title,
                        "zona_portada": "Sección - Canal 2",
                        "seccion": "Televisión",
                        "url": url,
                    }
                )

            except Exception as e:
                self.log(f"Error al procesar artículo de Canal 2: {e}", level="error")
                continue

        self.log(f"Se encontraron {len(articles)} titulares de Canal 2", level="info")
        return articles

    def _parse_el_pais_section(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extrae los artículos de la sección 'El país'"""
        articles = []
        # WARN: no va

        # Buscamos la sección por su título
        section_title = soup.find("h3", string="el país")
        print("section_title => ", section_title)
        if not section_title:
            self.log("No se encontró la sección 'El país'", level="warning")
            return articles

        # Buscamos el contenedor principal de los artículos
        section = section_title.find_parent("div", class_="row")
        print("section => ", section)
        if not section:
            return articles

        # Buscamos todos los artículos en esta sección
        articles_html = section.find_all("article", class_="nota")

        for article in articles_html:
            try:
                # Extraer el titular
                title_tag = article.find("h2", class_="font-medium")
                if not title_tag:
                    continue

                title = self.clean_text(title_tag.get_text(strip=True))
                if not title:
                    continue

                # Extraer la URL
                link = title_tag.find("a")
                if not link or not link.get("href"):
                    continue
                url = urljoin(self.url, link["href"])

                # Extraer la sección
                category_tag = article.find("h3", class_="nota__categoria")
                seccion = (
                    self.clean_text(category_tag.get_text(strip=True))
                    if category_tag
                    else "El país"
                )

                # Extraer la imagen si existe
                img_tag = article.find("img")
                img_url = img_tag["src"] if img_tag and img_tag.get("src") else ""

                articles.append(
                    {
                        "fecha": self.get_current_date(),
                        "medio": self.name,
                        "titular": title,
                        "zona_portada": "Sección - El país",
                        "seccion": seccion,
                        "url": url,
                        "imagen": img_url,
                    }
                )

            except Exception as e:
                self.log(f"Error al procesar artículo de 'El país': {e}", level="error")
                continue

        self.log(
            f"Se encontraron {len(articles)} artículos en la sección 'El país'",
            level="info",
        )
        return articles

    def _extract_article_data(
        self, article: Tag, zone_name: str
    ) -> Optional[Dict[str, Any]]:
        """Extrae los datos de un artículo individual"""
        try:
            # Extraer el titular
            title_tag = article.find(["h1", "h2"])
            if not title_tag:
                return None

            title = self.clean_text(title_tag.get_text(strip=True))
            if not title:
                return None

            # Extraer la URL
            link = title_tag.find("a")
            if not link or not link.get("href"):
                return None
            url = urljoin(self.url, link["href"])

            # Extraer la sección
            category_tag = article.find("h3", class_="nota__categoria")
            if category_tag:
                seccion = self.clean_text(category_tag.get_text(strip=True))
            else:
                seccion = self._extract_section_from_url(url)

            return {
                "fecha": self.get_current_date(),
                "medio": self.name,
                "titular": title,
                "zona_portada": zone_name,
                "seccion": seccion,
                "url": url,
            }
        except Exception as e:
            self.log(f"Error al procesar artículo en {zone_name}: {e}", level="error")
            return None

    def scrape(self) -> List[Dict[str, Any]]:
        """Método principal que realiza el scraping de La Capital"""
        self.log("Inicio del scraping de La Capital")
        news = []

        try:
            soup = self._get_soup(self.url)

            # Procesamos las secciones manteniendo la estructura original
            news.extend(self._parse_principal_section(soup))
            news.extend(self._parse_regular_sections(soup))
            news.extend(self._parse_ranking_section(soup))
            news.extend(self._parse_canal2_section(soup))
            news.extend(self._parse_el_pais_section(soup))

            self.log(f"Total de noticias encontradas: {len(news)}", level="info")
            return news

        except Exception as e:
            self.log(f"Error en el scraping: {e}", level="error")
            return []
