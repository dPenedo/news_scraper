from abc import ABC, abstractmethod
import logging
from typing import Optional, Dict, List, Any
from datetime import date
import requests


class NewsScraper(ABC):
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
    DEFAULT_TIMEOUT = 10

    def __init__(
        self,
        name: str,
        url: str,
        logger: Optional[logging.Logger] = None,
        user_agent: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.name = name
        self.url = url
        self.logger = logger or logging.getLogger("scraper")
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.timeout = timeout
        self.session = requests.Session()
        self._configure_session()

    def _configure_session(self) -> None:
        """Configura la sesión HTTP con los headers por defecto"""
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
        )

    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """Método principal que realiza el scraping.

        Returns:
            List[Dict[str, Any]]: Lista de diccionarios con la información de cada noticia,
                                 donde cada dict debe contener al menos:
                                 - fecha (str): Fecha en formato ISO
                                 - medio (str): Nombre del medio
                                 - titular (str): Título de la noticia
                                 - url (str): URL completa de la noticia
        """
        pass

    def log(self, message: str, level: str = "info") -> None:
        """Método helper para logging consistente."""
        if self.logger:
            log_method = getattr(self.logger, level, self.logger.info)
            log_method(f"[{self.name}] {message}")

    def get_current_date(self) -> str:
        """Devuelve la fecha actual en formato ISO."""
        return date.today().isoformat()

    def clean_text(self, text: str) -> str:
        """Limpia el texto eliminando espacios extras y caracteres especiales."""
        if not text:
            return ""
        return " ".join(text.strip().split())

    def close(self) -> None:
        """Cierra la sesión y libera recursos."""
        self.session.close()
        self.log("Sesión HTTP cerrada")

    def __enter__(self):
        """Permite usar la clase en un context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Garantiza que los recursos se liberan al salir del contexto."""
        self.close()
