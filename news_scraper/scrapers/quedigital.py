from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urljoin
import logging
import requests

from news_scraper.scrapers.base import NewsScraper


class QueDigitalScraper(NewsScraper):
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__(
            name="QueDigital",
            url="https://quedigital.com.ar",
            logger=logger,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",  # Actualizado a versión más reciente
        )

        # # Configuración de cookies (simulando consentimiento)
        # self.session.cookies.update({"cookie_consent": "true", "gdpr": "accepted"})
        #
        # # Deshabilitar verificación SSL si hay problemas (útil en entornos corporativos)
        # self.session.verify = False  # ¡Solo para desarrollo!

        # print(f"Requests version: {requests.__version__}")
        # print(f"Session headers: {self.session.headers}")

    def _get_soup(self, url: str) -> BeautifulSoup:
        """Obtiene el contenido HTML y lo parsea con BeautifulSoup"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = "utf-8"
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            self.log(f"Error al obtener la página: {e}", level="error")
            raise

    def _extract_section_from_url(self, url: str) -> str:
        """Extrae la categoría temática de la URL del artículo"""
        try:
            path = url.replace(self.url, "").strip("/")
            parts = path.split("/")
            return parts[0] if parts else "general"
        except Exception as e:
            self.log(f"Error al extraer categoría de {url}: {e}", level="warning")
            return "general"

    def _parse_featured_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae los artículos destacados"""
        articles = []
        featured_section = soup.find("div", id="featured")

        if not featured_section:
            self.log("No se encontró la sección de destacados", level="warning")
            return articles

        for post in featured_section.find_all("div", class_="et-featured-post"):
            try:
                title_tag = post.find("h2")
                if not title_tag or not title_tag.a:
                    continue

                title = self.clean_text(title_tag.get_text())
                url = urljoin(self.url, title_tag.a["href"])
                seccion = self._extract_section_from_url(url)

                articles.append(
                    {
                        "fecha": self.get_current_date(),
                        "medio": self.name,
                        "titular": title,
                        "zona_portada": "destacados_principal",
                        "seccion": seccion,
                        "url": url,
                    }
                )
            except Exception as e:
                self.log(f"Error al parsear artículo destacado: {e}", level="error")
                continue

        self.log(
            f"Se encontraron {len(articles)} artículos en destacados", level="info"
        )
        return articles

    def _parse_superfeatured_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae los artículos super destacados"""
        articles = []
        superfeatured_section = soup.find_all("div", class_="super-destacada")

        if not superfeatured_section:
            self.log(
                "No se encontró ninguna sección de super-destacada", level="warning"
            )
            return articles

        for i, section in enumerate(superfeatured_section, 1):
            # Buscar el h1 correcto que contiene el enlace (no el widgettitle)
            title_tags = section.find_all("h1")
            title_tag = next((tag for tag in title_tags if not tag.get("class")), None)
            if title_tag:
                try:
                    title = self.clean_text(title_tag.get_text())
                    url = urljoin(self.url, title_tag.a["href"])
                    seccion = self._extract_section_from_url(url)

                    articles.append(
                        {
                            "fecha": self.get_current_date(),
                            "medio": self.name,
                            "titular": title,
                            "zona_portada": "super-destacada",
                            "seccion": seccion,
                            "url": url,
                        }
                    )

                    self.log("Se encontro 1 artículo en super-destacada", level="info")

                except Exception as e:
                    self.log(
                        f"Error al parsear artículo super destacado: {e}", level="error"
                    )
                    continue

        return articles

    def _parse_recent_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae los artículos recientes"""
        articles = []
        recent_sections = soup.find_all("section", class_="recent-module")

        if not recent_sections:
            self.log("No se encontraron secciones de recientes", level="warning")
            return articles

        zone_names = {1: "recientes_superior", 2: "recientes_inferior"}

        for i, section in enumerate(recent_sections, 1):
            recent_posts = section.find_all("div", class_="recent-post")
            zone_name = zone_names.get(i, f"recientes_{i}")

            for post in recent_posts:
                try:
                    title_tag = post.find("h2")
                    if not title_tag or not title_tag.a:
                        continue

                    title = self.clean_text(title_tag.get_text())
                    url = urljoin(self.url, title_tag.a["href"])
                    seccion = self._extract_section_from_url(url)

                    articles.append(
                        {
                            "fecha": self.get_current_date(),
                            "medio": self.name,
                            "titular": title,
                            "zona_portada": zone_name,
                            "seccion": seccion,
                            "url": url,
                        }
                    )
                except Exception as e:
                    self.log(f"Error al parsear artículo reciente: {e}", level="error")
                    continue

            self.log(
                f"Se encontraron {len(recent_posts)} artículos en {zone_name}",
                level="info",
            )

        return articles

    def _parse_special_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae los artículos especiales"""
        articles = []
        special_sections = soup.find_all("div", class_=["especiales"])

        if not special_sections:
            self.log("No se encontraron secciones especiales", level="warning")
            return articles

        for section in special_sections:
            for widget in section.find_all("div", class_="widget_singlepostwidget"):
                try:
                    main_title = widget.find("h2", class_="titulogrupo")
                    if main_title:
                        title = self.clean_text(main_title.get_text())
                    else:
                        title_tag = widget.find("h2")
                        if not title_tag:
                            continue
                        title = self.clean_text(title_tag.get_text())

                    link = widget.find("a")
                    if not link or not link.get("href"):
                        continue

                    url = urljoin(self.url, link["href"])
                    category_tag = widget.find("div", class_="categ")
                    category = (
                        self.clean_text(category_tag.get_text())
                        if category_tag
                        else self._extract_section_from_url(url)
                    )

                    articles.append(
                        {
                            "fecha": self.get_current_date(),
                            "medio": self.name,
                            "titular": title,
                            "zona_portada": "especiales",
                            "seccion": category,
                            "url": url,
                        }
                    )
                except Exception as e:
                    self.log(f"Error al procesar artículo especial: {e}", level="error")
                    continue

        self.log(f"Se encontraron {len(articles)} artículos especiales", level="info")
        return articles

    def _parse_double_inferior_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae los artículos del grupo doble inferior"""
        articles = []
        section = soup.find("div", id="sidebar-grupo-doble-inferior")

        if not section:
            self.log("No se encontró la zona doble inferior", level="warning")
            return articles

        for post in section.find_all("div", class_="widget_singlepostwidget"):
            try:
                title_tag = post.find("h2", class_="titulogrupo")
                if not title_tag:
                    continue

                title = self.clean_text(title_tag.get_text())
                url = post.find("a")["href"] if post.find("a") else ""
                if not url:
                    continue

                url = urljoin(self.url, url)
                seccion = self._extract_section_from_url(url)

                articles.append(
                    {
                        "fecha": self.get_current_date(),
                        "medio": self.name,
                        "titular": title,
                        "zona_portada": "doble_inferior",
                        "seccion": seccion,
                        "url": url,
                    }
                )
            except Exception as e:
                self.log(
                    f"Error al parsear artículo doble inferior: {e}", level="error"
                )
                continue

        self.log(
            f"Se encontraron {len(articles)} artículos en doble_inferior", level="info"
        )
        return articles

    def _parse_quadruple_inferior_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae los artículos del grupo cuadruple inferior"""
        articles = []
        section = soup.find("div", id="sidebar-grupo-cuadruple-inferior")

        if not section:
            self.log("No se encontró la zona cuadruple inferior", level="warning")
            return articles

        for post in section.find_all("div", class_="widget_singlepostwidget"):
            try:
                title_tag = post.find("h2", class_="titulogrupo")
                if not title_tag:
                    continue

                title = self.clean_text(title_tag.get_text())
                url = post.find("a")["href"] if post.find("a") else ""
                if not url:
                    continue

                url = urljoin(self.url, url)
                seccion = self._extract_section_from_url(url)

                articles.append(
                    {
                        "fecha": self.get_current_date(),
                        "medio": self.name,
                        "titular": title,
                        "zona_portada": "triple_inferior",
                        "seccion": seccion,
                        "url": url,
                    }
                )
            except Exception as e:
                self.log(
                    f"Error al parsear artículo triple inferior: {e}", level="error"
                )
                continue

        self.log(
            f"Se encontraron {len(articles)} artículos en triple_inferior", level="info"
        )
        return articles

    def _parse_triple_inferior_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae los artículos del grupo triple inferior"""
        articles = []
        section = soup.find("div", id="sidebar-grupo-triple-inferior")

        if not section:
            self.log("No se encontró la zona triple inferior", level="warning")
            return articles

        for post in section.find_all("div", class_="widget_singlepostwidget"):
            try:
                title_tag = post.find("h2", class_="titulogrupo")
                if not title_tag:
                    continue

                title = self.clean_text(title_tag.get_text())
                url = post.find("a")["href"] if post.find("a") else ""
                if not url:
                    continue

                url = urljoin(self.url, url)
                seccion = self._extract_section_from_url(url)

                articles.append(
                    {
                        "fecha": self.get_current_date(),
                        "medio": self.name,
                        "titular": title,
                        "zona_portada": "triple_inferior",
                        "seccion": seccion,
                        "url": url,
                    }
                )
            except Exception as e:
                self.log(
                    f"Error al parsear artículo triple inferior: {e}", level="error"
                )
                continue

        self.log(
            f"Se encontraron {len(articles)} artículos en triple_inferior", level="info"
        )
        return articles

    def _parse_mas_vistas_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae los artículos más vistos"""
        articles = []
        mas_vistas_section = soup.find("div", class_="widget popular-posts")

        if not mas_vistas_section:
            self.log("No se encontró la sección de más vistas", level="warning")
            return articles

        for item in mas_vistas_section.find_all("li"):
            try:
                link = item.find("a", class_="wpp-post-title")
                if not link:
                    continue

                title = self.clean_text(link.get_text())
                url = urljoin(self.url, link["href"])
                seccion = self._extract_section_from_url(url)

                articles.append(
                    {
                        "fecha": self.get_current_date(),
                        "medio": self.name,
                        "titular": title,
                        "zona_portada": "mas_vistas",
                        "seccion": seccion,
                        "url": url,
                    }
                )
            except Exception as e:
                self.log(f"Error al procesar artículo más visto: {e}", level="error")
                continue

        self.log(
            f"Se encontraron {len(articles)} artículos en mas_vistas", level="info"
        )
        return articles

    def _parse_deportes_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae los artículos de deportes"""
        articles = []
        section = soup.find("section", class_="recent-deportes")

        if not section:
            self.log("No se encontró la zona deportes", level="warning")
            return articles

        for post in section.find_all("div", class_="recent-deporte"):
            try:
                title_tag = post.find("h2")
                if not title_tag or not title_tag.a:
                    continue

                title = self.clean_text(title_tag.get_text())
                url = urljoin(self.url, title_tag.a["href"])
                seccion = self._extract_section_from_url(url)

                articles.append(
                    {
                        "fecha": self.get_current_date(),
                        "medio": self.name,
                        "titular": title,
                        "zona_portada": "deportes",
                        "seccion": seccion,
                        "url": url,
                    }
                )
            except Exception as e:
                self.log(f"Error al parsear artículo de deportes: {e}", level="error")
                continue

        self.log(f"Se encontraron {len(articles)} artículos en deportes", level="info")
        return articles

    def _parse_cultura_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae los artículos de cultura"""
        articles = []
        section = soup.find("section", class_="recent-cultura")

        if not section:
            self.log("No se encontró la zona cultura", level="warning")
            return articles

        for post in section.find_all("div", class_="recent-cul"):
            try:
                title_tag = post.find("h2")
                if not title_tag or not title_tag.a:
                    continue

                title = self.clean_text(title_tag.get_text())
                url = urljoin(self.url, title_tag.a["href"])
                seccion = self._extract_section_from_url(url)

                articles.append(
                    {
                        "fecha": self.get_current_date(),
                        "medio": self.name,
                        "titular": title,
                        "zona_portada": "cultura",
                        "seccion": seccion,
                        "url": url,
                    }
                )
            except Exception as e:
                self.log(f"Error al parsear artículo de cultura: {e}", level="error")
                continue

        self.log(f"Se encontraron {len(articles)} artículos en cultura", level="info")
        return articles

    def scrape(self) -> List[Dict]:
        """Método principal que realiza el scraping"""
        self.log("Inicio del scraping de QueDigital")
        titulares = []

        try:
            with self:  # Usamos el context manager
                soup = self._get_soup(self.url)

                parsing_methods = [
                    self._parse_featured_articles,
                    self._parse_recent_articles,
                    self._parse_special_articles,
                    self._parse_superfeatured_articles,
                    self._parse_double_inferior_articles,
                    self._parse_quadruple_inferior_articles,
                    self._parse_triple_inferior_articles,
                    self._parse_mas_vistas_articles,
                    self._parse_deportes_articles,
                    self._parse_cultura_articles,
                ]

                for method in parsing_methods:
                    try:
                        titulares.extend(method(soup))
                    except Exception as e:
                        self.log(f"Error en {method.__name__}: {e}", level="error")
                        continue

                self.log(f"Total de titulares encontrados: {len(titulares)}")

        except Exception as e:
            self.log(f"Error durante el scraping: {e}", level="error")
            raise

        self.log("Fin del scraping")
        return titulares
