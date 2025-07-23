from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Optional, cast
from urllib.parse import urljoin
import logging
import requests

from news_scraper.scrapers.base import NewsScraper


class CerodosdostresScraper(NewsScraper):
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__(
            name="0223",
            url="https://www.0223.com.ar",
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

    def _parse_generic_article(
        self, article_tag: Tag, zone_name: str
    ) -> Optional[Dict[str, str]]:
        """Método genérico para parsear cualquier artículo"""
        try:
            article_tag = cast(Tag, article_tag)
            title_tag = article_tag.find("h2", class_="nota__titulo-item")
            if not title_tag:
                return None

            title = self.clean_text(title_tag.get_text())

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
                seccion = self.clean_text(volanta.a.p.get_text())
            else:
                seccion = zone_name.rsplit("_", 1)[0]

            return {
                "fecha": self.get_current_date(),
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
        secondary_articles = apertura_section.find("div", class_="notas-secundarias")
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

        # Encontrar el bloque de notas para desktop
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

                title = self.clean_text(title_tag.get_text())
                url = (
                    urljoin(self.url, title_tag.parent["href"])
                    if title_tag.parent
                    else ""
                )

                articles.append(
                    {
                        "fecha": self.get_current_date(),
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

    def _parse_bloque_3notas_sections(
        self, soup: BeautifulSoup
    ) -> List[Dict[str, str]]:
        """Extrae los artículos de todas las secciones con la clase 'bloque-3Notas'."""
        articles: List[Dict[str, str]] = []

        bloque_3notas_sections = soup.find_all("div", class_="bloque-3Notas")

        if not bloque_3notas_sections:
            self.log(
                "No se encontraron secciones con la clase 'bloque-3Notas'.",
                level="warning",
            )
            return articles

        for section_idx, section_container in enumerate(bloque_3notas_sections):
            section_name = f"bloque_3notas_{section_idx + 1}"  # Nombre genérico de la sección por defecto

            # Intentar encontrar el título de la sección (por ejemplo, "Columnas")
            title_block = section_container.find("div", class_="titulo_bloque")
            if title_block:
                title_link = title_block.find("a")
                if title_link and title_link.get_text():
                    section_name = (
                        self.clean_text(title_link.get_text()).replace(" ", "_").lower()
                    )

            # Buscar el div.grid que contiene los artículos (item-4) dentro de este contenedor.
            seccion_grid = section_container.find("div", class_="grid")

            if not seccion_grid:
                self.log(
                    f"No se encontró el 'div.grid' dentro del bloque '{section_name}'.",
                    level="warning",
                )
                continue  # Pasar a la siguiente sección si no se encuentra el grid

            # Buscar todos los div.item-4 que contienen los artículos dentro de este div.grid
            items = seccion_grid.find_all("div", class_="item-4")

            if not items:
                self.log(
                    f"No se encontraron elementos 'item-4' dentro de la sección '{section_name}'.",
                    level="warning",
                )
                continue  # Pasar a la siguiente sección si no hay items

            for i, item in enumerate(items, 1):
                try:
                    article_tag = item.find("article", class_="nota--gral")
                    if not article_tag:
                        continue

                    # Usar el nombre de la sección identificada como default_section para _parse_generic_article
                    article_data = self._parse_generic_article(
                        cast(Tag, article_tag),
                        f"{section_name}_{i}",
                    )
                    if article_data:
                        articles.append(article_data)

                except Exception as e:
                    self.log(
                        f"Error al parsear artículo {i} de la sección '{section_name}': {e}",
                        level="error",
                    )
                    continue

        self.log(
            f"Se encontraron {len(articles)} artículos en las secciones 'bloque-3notas (Virales y columnas)'.",
            level="info",
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

    def _parse_liga_profesional(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extrae los artículos de la sección Liga Profesional"""
        articles: List[Dict[str, str]] = []
        liga_section = soup.find("div", class_="bloque-mundial")

        if not liga_section:
            self.log("No se encontró la sección de Liga Profesional", level="warning")
            return articles

        # Buscar el contenedor de notas dentro de la sección
        notas_container = liga_section.find("div", class_="mundial-notasFijas")
        if not notas_container:
            self.log(
                "No se encontró el contenedor de notas en Liga Profesional",
                level="warning",
            )
            return articles

        # Procesar todos los artículos
        for i, article_tag in enumerate(notas_container.find_all("article"), 1):
            try:
                # Determinar el tipo de artículo (principal o secundario)
                if "nota--gral" in article_tag.get("class", []):
                    article_type = "principal"
                else:
                    article_type = f"secundaria_{i}"

                article_data = self._parse_generic_article(
                    cast(Tag, article_tag), f"liga_profesional_{article_type}"
                )

                if article_data:
                    # Si es la nota principal, asegurarnos de que la sección sea "Liga Profesional"
                    if article_type == "principal":
                        article_data["seccion"] = "Liga Profesional"
                    articles.append(article_data)

            except Exception as e:
                self.log(
                    f"Error al parsear artículo {i} de Liga Profesional: {e}",
                    level="error",
                )
                continue

        self.log(
            f"Se encontraron {len(articles)} artículos en Liga Profesional",
            level="info",
        )
        return articles

    def _parse_notas_relleno(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extrae los artículos de los bloques 'relleno' que contienen notas variadas"""
        articles: List[Dict[str, str]] = []

        # Buscar todos los bloques relleno
        bloques_relleno = soup.find_all("div", class_="relleno")

        if not bloques_relleno:
            self.log("No se encontraron bloques 'relleno'", level="warning")
            return articles

        for bloque_idx, bloque in enumerate(bloques_relleno, 1):
            # Buscar el contenedor de notas dentro de cada bloque relleno
            bloque_notas = bloque.find("div", class_="bloque-notas")
            if not bloque_notas:
                continue

            # Procesar todos los artículos dentro del bloque
            for i, article_tag in enumerate(
                bloque_notas.find_all("article", class_="nota--relleno"), 1
            ):
                try:
                    article_data = self._parse_generic_article(
                        cast(Tag, article_tag), f"relleno_{bloque_idx}_{i}"
                    )

                    if article_data:
                        # Si hay una volantaTop, usarla como sección
                        volanta_top = article_tag.find("div", class_="nota__volantaTop")
                        if volanta_top and volanta_top.a and volanta_top.a.p:
                            article_data["seccion"] = self.clean_text(
                                volanta_top.a.p.get_text()
                            )

                        articles.append(article_data)

                except Exception as e:
                    self.log(
                        f"Error al parsear artículo {i} del bloque relleno {bloque_idx}: {e}",
                        level="error",
                    )
                    continue

        self.log(
            f"Se encontraron {len(articles)} artículos en bloques 'relleno'",
            level="info",
        )
        return articles

    def _parse_bloque_sabana(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extrae los artículos del bloque 'bloque_sabana'"""
        articles: List[Dict[str, str]] = []
        bloque_sabana = soup.find("div", class_="bloque_sabana")

        if not bloque_sabana:
            self.log("No se encontró el bloque 'bloque_sabana'", level="warning")
            return articles

        # Buscar el contenedor de notas dentro del bloque
        bloque_notas = bloque_sabana.find("div", class_="bloque-notas")
        if not bloque_notas:
            self.log(
                "No se encontró el contenedor de notas en bloque_sabana",
                level="warning",
            )
            return articles

        # Procesar todos los artículos dentro del bloque
        for i, article_tag in enumerate(
            bloque_notas.find_all("article", class_="nota--relleno"), 1
        ):
            try:
                article_data = self._parse_generic_article(
                    cast(Tag, article_tag), f"bloque_sabana_{i}"
                )

                if article_data:
                    # Si hay una volantaTop, usarla como sección
                    volanta_top = article_tag.find("div", class_="nota__volantaTop")
                    if volanta_top and volanta_top.a and volanta_top.a.p:
                        article_data["seccion"] = self.clean_text(
                            volanta_top.a.p.get_text()
                        )

                    articles.append(article_data)

            except Exception as e:
                self.log(
                    f"Error al parsear artículo {i} del bloque_sabana: {e}",
                    level="error",
                )
                continue

        self.log(
            f"Se encontraron {len(articles)} artículos en bloque_sabana", level="info"
        )
        return articles

    def _parse_d_4notas(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extrae los artículos del bloque 'd_4Notas'"""
        articles: List[Dict[str, str]] = []
        d_4notas = soup.find("div", class_="d_4Notas")

        if not d_4notas:
            self.log("No se encontró el bloque 'd_4Notas'", level="warning")
            return articles

        # Buscar el contenedor de notas dentro del bloque
        grid_relleno = d_4notas.find("div", class_="grid relleno")
        if not grid_relleno:
            self.log(
                "No se encontró el contenedor de notas en d_4Notas", level="warning"
            )
            return articles

        # Procesar todos los artículos dentro del bloque
        for i, article_tag in enumerate(
            grid_relleno.find_all("article", class_="nota--relleno"), 1
        ):
            try:
                article_data = self._parse_generic_article(
                    cast(Tag, article_tag), f"d_4notas_{i}"
                )

                if article_data:
                    # Si hay una volantaTop, usarla como sección
                    volanta_top = article_tag.find("div", class_="nota__volantaTop")
                    if volanta_top and volanta_top.a and volanta_top.a.p:
                        article_data["seccion"] = self.clean_text(
                            volanta_top.a.p.get_text()
                        )

                    articles.append(article_data)

            except Exception as e:
                self.log(
                    f"Error al parsear artículo {i} del bloque d_4Notas: {e}",
                    level="error",
                )
                continue

        self.log(f"Se encontraron {len(articles)} artículos en d_4Notas", level="info")
        return articles

    # Métodos específicos para cada sección
    def _parse_mar_del_plata_section(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        return self._parse_section(soup, "mar_del_plata", "/mar-del-plata")

    def _parse_argentina_section(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        return self._parse_section(soup, "argentina", "/mas-alla-de-la-ciudad")

    def _parse_seguridad_section(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        return self._parse_section(soup, "seguridad", "/seguridad")

    def _parse_edicion_5_section(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        return self._parse_section(soup, "edicion5", "/edicion5")

    def _parse_deportes_section(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        return self._parse_section(soup, "deportes", "/deportes")

    def _parse_espectaculos_section(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        return self._parse_section(soup, "espectaculos", "/arte-espectaculos")

    def scrape(self) -> List[Dict[str, str]]:
        """Método principal que realiza el scraping"""
        self.log("Inicio del scraping de 0223")
        titulares: List[Dict[str, str]] = []

        try:
            with self:  # Usamos el context manager para manejo de recursos
                soup = self._get_soup(self.url)

                # Obtener artículos de todas las secciones
                parsing_methods = [
                    self._parse_apertura_articles,
                    self._parse_notas_relleno,  # contiene dos bloques de 8
                    self._parse_mar_del_plata_section,
                    self._parse_argentina_section,
                    self._parse_seguridad_section,
                    self._parse_deportes_section,
                    self._parse_propiedades_section,
                    self._parse_espectaculos_section,
                    self._parse_mas_leidas,
                    self._parse_historias_aca,
                    self._parse_edicion_5_section,
                    self._parse_bloque_3notas_sections,  # Virales y columnas
                    self._parse_bloque_sabana,  # 4 notas debajo de columnas
                    self._parse_liga_profesional,
                    self._parse_d_4notas,  # 4 notas debajo de la liga
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
