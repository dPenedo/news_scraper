from logging import Logger
from news_scraper.scrapers.base import NewsScraper
from datetime import date
from bs4 import BeautifulSoup, Tag
import requests
from typing import List, Dict, Optional, cast
from urllib.parse import urljoin


class CerodosdostresScraper(NewsScraper):
    def __init__(self, logger: Optional[Logger] = None):
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

    def _parse_generic_article(
        self, article_tag: Tag, zone_name: str
    ) -> Optional[Dict[str, str]]:
        """Método genérico para parsear cualquier artículo"""
        try:
            # Convertir a Tag para ayudar al type checker
            article_tag = cast(Tag, article_tag)

            title_tag = article_tag.find("h2", class_="nota__titulo-item")
            if not title_tag:
                return None

            title = title_tag.get_text(strip=True)

            # El enlace puede estar en el título o en el contenedor principal
            link_tag: Optional[Tag] = None
            if title_tag.parent and title_tag.parent.name == "a":
                link_tag = cast(Tag, title_tag.parent)
            else:
                link_tag = article_tag.find("a", class_="nota__media--link")

            if not link_tag or not link_tag.get("href"):
                return None

            url = urljoin(self.url, cast(str, link_tag["href"]))

            # Extraer sección
            volanta = article_tag.find("div", class_="nota__volanta")
            seccion = ""
            if volanta and volanta.a and volanta.a.p:
                seccion = volanta.a.p.get_text(strip=True)
            else:
                seccion = zone_name.rsplit("_", 1)[0]

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
    ) -> List[Dict[str, str]]:
        """Método genérico para extraer artículos de cualquier sección"""
        articles: List[Dict[str, str]] = []

        # Buscar el contenedor de la sección
        section_container = soup.select_one(f'div.grid:has(a[href="{section_path}"])')
        if not section_container:
            self.log(f"No se encontró la sección {section_name}", level="warning")
            return articles

        # Procesar todos los artículos de la sección
        for i, article_tag in enumerate(section_container.find_all("article"), 1):
            article_tag = cast(Tag, article_tag)
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

    def _parse_apertura_articles(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extrae los artículos de la sección apertura (destacados)"""
        main_title = ""
        articles: List[Dict[str, str]] = []
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
                    cast(Tag, article_tag), "apertura_principal"
                )
                if article_data:
                    main_title = article_data["titular"]
                    articles.append(article_data)

        # Artículos secundarios
        secondary_articles = apertura_section.find(
            "div", class_="notas-secundarias"
        )  # Aqui => un breakpoint
        if secondary_articles:
            for i, article_tag in enumerate(
                secondary_articles.find_all("article", class_="nota--gral"), 1
            ):
                article_data = self._parse_generic_article(
                    cast(Tag, article_tag), f"apertura_secundaria_{i}"
                )
                if article_data and article_data["titular"] != main_title:
                    articles.append(article_data)

        self.log(f"Se encontraron {len(articles)} artículos en apertura", level="info")
        return articles

    def _parse_bloque_notas(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extrae los artículos del bloque de notas (sección inferior)"""
        articles: List[Dict[str, str]] = []
        bloque_notas = soup.find("div", class_="bloque-notas")

        if not bloque_notas:
            self.log("No se encontró el bloque de notas", level="warning")
            return articles

        for i, article_tag in enumerate(
            bloque_notas.find_all("article", class_="nota--linea"), 1
        ):
            article_data = self._parse_generic_article(
                cast(Tag, article_tag), f"bloque_notas_{i}"
            )
            if article_data:
                articles.append(article_data)

        self.log(
            f"Se encontraron {len(articles)} artículos en bloque de notas", level="info"
        )
        return articles

    def _parse_propiedades_section(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extrae los artículos de la sección Propiedades"""
        articles: List[Dict[str, str]] = []
        propiedades_section = soup.find("div", class_="bloque-prop")

        if not propiedades_section:
            self.log("No se encontró la sección de Propiedades", level="warning")
            return articles

        # Artículo principal
        main_article = propiedades_section.find("article", class_="nota--especial")
        if main_article:
            article_data = self._parse_generic_article(
                cast(Tag, main_article), "propiedades_principal"
            )
            if article_data:
                articles.append(article_data)

        # Artículos secundarios
        secondary_articles = propiedades_section.find_all(
            "article", class_="nota--linea"
        )
        for i, article_tag in enumerate(secondary_articles, 1):
            article_data = self._parse_generic_article(
                cast(Tag, article_tag), f"propiedades_secundaria_{i}"
            )
            if article_data:
                articles.append(article_data)

        self.log(
            f"Se encontraron {len(articles)} artículos en Propiedades", level="info"
        )
        return articles

    def _parse_mas_leidas(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extrae las 5 noticias más leídas"""
        articles: List[Dict[str, str]] = []
        mas_leidas_section = soup.find("div", class_="mas_leidas")

        if not mas_leidas_section:
            self.log("No se encontró la sección de Más Leídas", level="warning")
            return articles

        # Encontrar el bloque de notas para desktop (contiene las 5 más leídas)
        bloque_notas = mas_leidas_section.find("div", class_="bloque-notas-desktop")
        if not bloque_notas:
            self.log("No se encontró el bloque de notas más leídas", level="warning")
            return articles

        # Extraer cada artículo
        for article_tag in bloque_notas.find_all("article", class_="nota--linea"):
            try:
                # Obtener el ranking (1-5)
                contador_tag = article_tag.find("div", class_="nota__contador")
                ranking = contador_tag.get_text(strip=True) if contador_tag else "0"

                # Obtener título y URL
                title_tag = article_tag.find("h2", class_="nota__titulo-item")
                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)
                url = (
                    urljoin(self.url, title_tag.parent["href"])
                    if title_tag.parent
                    else ""
                )

                articles.append(
                    {
                        "fecha": date.today().isoformat(),
                        "medio": self.name,
                        "titular": title,
                        "zona_portada": f"mas_leidas_{ranking}",
                        "seccion": "Más Leídas",
                        "url": url,
                    }
                )

            except Exception as e:
                self.log(f"Error al parsear artículo más leído: {e}", level="error")
                continue

        self.log(
            f"Se encontraron {len(articles)} artículos en Más Leídas", level="info"
        )
        return articles

    def _parse_historias_aca(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extrae los artículos de la sección 'Historias de acá'"""
        articles: List[Dict[str, str]] = []

        try:
            historias_section = soup.find("div", class_="bloque-historiasAca")

            if not historias_section:
                self.log(
                    "No se encontró la sección 'Historias de acá'", level="warning"
                )
                return articles

            # Artículo principal (nota--especial)
            main_article = historias_section.find("article", class_="nota--especial")
            if main_article:
                try:
                    article_data = self._parse_generic_article(
                        cast(Tag, main_article), "historias_aca_principal"
                    )
                    if article_data:
                        articles.append(article_data)
                except Exception as e:
                    self.log(
                        f"Error al parsear artículo principal de Historias de acá: {e}",
                        level="error",
                    )

            # Artículos secundarios (nota--linea)
            secondary_articles = historias_section.find_all(
                "article", class_="nota--linea"
            )
            for i, article_tag in enumerate(secondary_articles, 1):
                try:
                    article_data = self._parse_generic_article(
                        cast(Tag, article_tag), f"historias_aca_secundaria_{i}"
                    )
                    if article_data:
                        articles.append(article_data)
                except Exception as e:
                    self.log(
                        f"Error al parsear artículo secundario {i} de Historias de acá: {e}",
                        level="error",
                    )
                    continue

        except Exception as e:
            self.log(
                f"Error inesperado al procesar sección Historias de acá: {e}",
                level="error",
            )

        self.log(
            f"Se encontraron {len(articles)} artículos en 'Historias de acá'",
            level="info",
        )
        return articles

    def _parse_columnas_section(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extrae los artículos de la sección Columnas"""
        articles: List[Dict[str, str]] = []

        try:
            # 1. Encontrar el título "Columnas"
            titulo_columnas = soup.find("a", href="/columnas", string="Columnas")
            if not titulo_columnas:
                self.log("No se encontró el título de Columnas", level="warning")
                return articles

            # 2. Subir hasta el div.grid que contiene tanto el título como los artículos
            contenedor_titulo = titulo_columnas.find_parent("div", class_="item-12")
            if not contenedor_titulo:
                self.log(
                    "No se encontró el contenedor del título de Columnas",
                    level="warning",
                )
                return articles

            seccion_columnas = contenedor_titulo.find_parent("div", class_="grid")
            if not seccion_columnas:
                self.log(
                    "No se encontró el contenedor principal de Columnas",
                    level="warning",
                )
                return articles

            # 3. Buscar todos los div.item-4 que contienen los artículos
            items_columnas = seccion_columnas.find_all("div", class_="item-4")

            for i, item in enumerate(items_columnas, 1):
                try:
                    article_tag = item.find("article", class_="nota--gral")
                    if not article_tag:
                        continue

                    # Extraer datos del artículo
                    title_tag = article_tag.find("h2", class_="nota__titulo-item")
                    if not title_tag:
                        continue

                    title = title_tag.get_text(strip=True)

                    # Obtener URL
                    link_tag = article_tag.find(
                        "a", class_="nota__media--link"
                    ) or title_tag.find_parent("a")
                    if not link_tag or not link_tag.get("href"):
                        continue

                    url = urljoin(self.url, link_tag["href"])

                    # Extraer sección específica (ej. "El Escribiente")
                    volanta_tag = article_tag.find("div", class_="nota__volanta")
                    seccion = "Columnas"  # Valor por defecto
                    if volanta_tag and volanta_tag.a and volanta_tag.a.p:
                        seccion = volanta_tag.a.p.get_text(strip=True)

                    articles.append(
                        {
                            "fecha": date.today().isoformat(),
                            "medio": self.name,
                            "titular": title,
                            "zona_portada": f"columnas_{i}",
                            "seccion": seccion,
                            "url": url,
                        }
                    )

                except Exception as e:
                    self.log(
                        f"Error al parsear artículo {i} de Columnas: {e}", level="error"
                    )
                    continue

        except Exception as e:
            self.log(
                f"Error inesperado al procesar sección Columnas: {e}", level="error"
            )

        self.log(f"Se encontraron {len(articles)} artículos en Columnas", level="info")
        return articles

    # Métodos específicos para cada sección
    def _parse_mar_del_plata_section(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        return self._parse_section(soup, "mar_del_plata", "/mar-del-plata")

    def _parse_argentina_section(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        return self._parse_section(soup, "argentina", "/mas-alla-de-la-ciudad")

    def _parse_seguridad_section(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        return self._parse_section(soup, "seguridad", "/seguridad")

    def _parse_deportes_section(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        return self._parse_section(soup, "deportes", "/deportes")

    def _parse_espectaculos_section(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        return self._parse_section(soup, "espectaculos", "/arte-espectaculos")

    def scrape(self) -> List[Dict[str, str]]:
        """Método principal que realiza el scraping"""
        self.log("Inicio del scraping de 0223")
        titulares: List[Dict[str, str]] = []

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
            titulares.extend(self._parse_propiedades_section(soup))
            titulares.extend(self._parse_mas_leidas(soup))
            titulares.extend(self._parse_historias_aca(soup))
            titulares.extend(self._parse_columnas_section(soup))

            self.log(f"Total de titulares encontrados: {len(titulares)}")

        except Exception as e:
            self.log(f"Error durante el scraping: {e}", level="error")
            raise

        self.log("Fin del scraping")
        return titulares
