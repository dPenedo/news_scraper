from news_scraper.scrapers.base import NewsScraper
from datetime import date
from bs4 import BeautifulSoup
import requests
from typing import List, Dict
from urllib.parse import urljoin


class QueDigitalScraper(NewsScraper):
    def __init__(self, logger=None):
        super().__init__("QueDigital", "https://quedigital.com.ar", logger)
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

    def _extract_section_from_url(self, url: str) -> str:
        """Extrae la categoría temática de la URL del artículo"""
        try:
            # Eliminamos la URL base y dividimos por /
            path = url.replace(self.url, "").strip("/")
            parts = path.split("/")
            # La categoría es normalmente la primera parte después del dominio
            return parts[0] if parts else "general"
        except Exception as e:
            self.log(f"Error al extraer categoría de {url}: {e}", level="warning")
            return "general"

    def _parse_featured_articles(self, soup: BeautifulSoup) -> list[dict]:
        """extrae los artículos destacados"""
        articles = []
        featured_section = soup.find("div", id="featured")

        if not featured_section:
            self.log("no se encontró la sección de destacados", level="warning")
            return articles

        featured_posts = featured_section.find_all("div", class_="et-featured-post")

        for post in featured_posts:
            try:
                title_tag = post.find("h2")
                if not title_tag or not title_tag.a:
                    continue

                title = title_tag.get_text(strip=True)
                url = title_tag.a["href"]
                url = urljoin(self.url, url)

                seccion = self._extract_section_from_url(url)

                articles.append(
                    {
                        "fecha": date.today().isoformat(),
                        "medio": self.name,
                        "titular": title,
                        "zona_portada": "destacados_principal",
                        "seccion": seccion,
                        "url": url,
                    }
                )
            except Exception as e:
                self.log(f"error al parsear artículo destacado: {e}", level="error")
                continue

        self.log(
            f"se encontraron {len(articles)} artículos en destacados_principal",
            level="info",
        )
        return articles

    def _parse_recent_articles(self, soup: BeautifulSoup) -> list[dict]:
        """extrae los artículos recientes de todas las secciones recent-module"""
        articles = []
        recent_sections = soup.find_all("section", class_="recent-module")

        if not recent_sections:
            self.log("no se encontraron secciones de recientes", level="warning")
            return articles

        # nombres más descriptivos para las zonas
        zone_names = {1: "recientes_superior", 2: "recientes_inferior"}

        for i, section in enumerate(recent_sections, 1):
            recent_posts = section.find_all("div", class_="recent-post")
            zone_name = zone_names.get(i, f"recientes_{i}")

            for post in recent_posts:
                try:
                    title_tag = post.find("h2")
                    if not title_tag or not title_tag.a:
                        continue

                    title = title_tag.get_text(strip=True)
                    url = title_tag.a["href"]
                    url = urljoin(self.url, url)

                    # extraemos la sección temática de la url
                    seccion = self._extract_section_from_url(url)

                    articles.append(
                        {
                            "fecha": date.today().isoformat(),
                            "medio": self.name,
                            "titular": title,
                            "zona_portada": zone_name,  # ubicación en portada
                            "seccion": seccion,  # temática del artículo
                            "url": url,
                        }
                    )
                except Exception as e:
                    self.log(
                        f"error al parsear artículo reciente en zona {zone_name}: {e}",
                        level="error",
                    )
                    continue

            self.log(
                f"se encontraron {len(recent_posts)} artículos en zona {zone_name}",
                level="info",
            )

        return articles

    def _parse_special_articles(self, soup: BeautifulSoup) -> list[dict]:
        """Extrae los artículos especiales de las secciones con class 'especiales'"""
        articles = []

        # Encontrar todas las secciones especiales
        special_sections = soup.find_all("div", class_=["especiales"])

        if not special_sections:
            self.log("No se encontraron secciones especiales", level="warning")
            return articles

        # Procesar cada sección especial
        for section in special_sections:
            # Encontrar todos los widgets de artículos especiales
            special_widgets = section.find_all("div", class_="widget_singlepostwidget")

            for widget in special_widgets:
                try:
                    # Extraer el título principal (h2.titulogrupo)
                    main_title = widget.find("h2", class_="titulogrupo")
                    if main_title:
                        title = main_title.get_text(strip=True)
                    else:
                        # Si no hay título principal, buscar el título normal
                        title_tag = widget.find("h2")
                        if not title_tag:
                            continue
                        title = title_tag.get_text(strip=True)

                    # Extraer URL
                    link = widget.find("a")
                    if not link or not link.get("href"):
                        continue

                    url = urljoin(self.url, link["href"])

                    # Extraer la categoría/sección
                    category_tag = widget.find("div", class_="categ")
                    category = (
                        category_tag.get_text(strip=True)
                        if category_tag
                        else self._extract_section_from_url(url)
                    )

                    articles.append(
                        {
                            "fecha": date.today().isoformat(),
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

        posts = section.find_all("div", class_="widget_singlepostwidget")

        for post in posts:
            try:
                title_tag = post.find("h2", class_="titulogrupo")
                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)
                url = post.find("a")["href"] if post.find("a") else ""
                if not url:
                    continue

                url = urljoin(self.url, url)
                seccion = self._extract_section_from_url(url)

                articles.append(
                    {
                        "fecha": date.today().isoformat(),
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
            f"Se encontraron {len(articles)} artículos en zona doble_inferior",
            level="info",
        )
        return articles

    def _parse_triple_inferior_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae los artículos del grupo triple inferior"""
        articles = []
        section = soup.find("div", id="sidebar-grupo-triple-inferior")

        if not section:
            self.log("No se encontró la zona triple inferior", level="warning")
            return articles

        posts = section.find_all("div", class_="widget_singlepostwidget")

        for post in posts:
            try:
                title_tag = post.find("h2", class_="titulogrupo")
                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)
                url = post.find("a")["href"] if post.find("a") else ""
                if not url:
                    continue

                url = urljoin(self.url, url)
                seccion = self._extract_section_from_url(url)

                articles.append(
                    {
                        "fecha": date.today().isoformat(),
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
            f"Se encontraron {len(articles)} artículos en zona triple_inferior",
            level="info",
        )
        return articles

    def _parse_mas_vistas_articles(self, soup: BeautifulSoup) -> list[dict]:
        """Extrae los artículos de la sección 'LAS MÁS VISTAS'"""
        articles = []

        # Encontrar la sección de más vistas
        mas_vistas_section = soup.find("div", class_="widget popular-posts")

        if not mas_vistas_section:
            self.log("No se encontró la sección de más vistas", level="warning")
            return articles

        # Encontrar todos los items de la lista
        items = mas_vistas_section.find_all("li")

        for item in items:
            try:
                # Extraer el enlace y título
                link = item.find("a", class_="wpp-post-title")
                if not link:
                    continue

                title = link.get_text(strip=True)
                url = link["href"]
                url = urljoin(self.url, url)

                print("title => ", title)
                # Extraer la sección temática de la url
                seccion = self._extract_section_from_url(url)

                articles.append(
                    {
                        "fecha": date.today().isoformat(),
                        "medio": self.name,
                        "titular": title,
                        "zona_portada": "mas_vistas",
                        "seccion": seccion,
                        "url": url,
                    }
                )
            except Exception as e:
                self.log(
                    f"Error al procesar artículo de más vistas: {e}", level="error"
                )
                continue

        self.log(
            f"Se encontraron {len(articles)} artículos en las_mas_vistas", level="info"
        )
        return articles

    def _parse_deportes_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae los artículos de deportes"""
        articles = []
        section = soup.find("section", class_="recent-deportes")

        if not section:
            self.log("No se encontró la zona deportes", level="warning")
            return articles

        posts = section.find_all("div", class_="recent-deporte")

        for post in posts:
            try:
                title_tag = post.find("h2")
                if not title_tag or not title_tag.a:
                    continue

                title = title_tag.get_text(strip=True)
                url = title_tag.a["href"]
                url = urljoin(self.url, url)
                seccion = self._extract_section_from_url(url)

                articles.append(
                    {
                        "fecha": date.today().isoformat(),
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

        self.log(
            f"Se encontraron {len(articles)} artículos en zona deportes", level="info"
        )
        return articles

    def _parse_cultura_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae los artículos de cultura"""
        articles = []
        section = soup.find("section", class_="recent-cultura")

        if not section:
            self.log("No se encontró la zona cultura", level="warning")
            return articles

        posts = section.find_all("div", class_="recent-cul")

        for post in posts:
            try:
                title_tag = post.find("h2")
                if not title_tag or not title_tag.a:
                    continue

                title = title_tag.get_text(strip=True)
                url = title_tag.a["href"]
                url = urljoin(self.url, url)
                seccion = self._extract_section_from_url(url)

                articles.append(
                    {
                        "fecha": date.today().isoformat(),
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

        self.log(
            f"Se encontraron {len(articles)} artículos en zona cultura", level="info"
        )
        return articles

    def scrape(self) -> list[dict]:
        """método principal que realiza el scraping"""
        self.log("inicio del scraping de quedigital")
        titulares = []

        try:
            soup = self._get_soup(self.url)

            # obtener todas las secciones
            titulares.extend(self._parse_featured_articles(soup))
            titulares.extend(self._parse_recent_articles(soup))
            titulares.extend(
                self._parse_special_articles(soup)
            )  # Añadido para artículos especiales
            titulares.extend(self._parse_double_inferior_articles(soup))
            titulares.extend(self._parse_triple_inferior_articles(soup))
            titulares.extend(self._parse_mas_vistas_articles(soup))
            titulares.extend(self._parse_deportes_articles(soup))
            titulares.extend(self._parse_cultura_articles(soup))

            self.log(f"total de titulares encontrados: {len(titulares)}")

        except Exception as e:
            self.log(f"error durante el scraping: {e}", level="error")
            raise

        self.log("fin del scraping")
        return titulares
