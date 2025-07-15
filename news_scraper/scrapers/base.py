from abc import ABC, abstractmethod
import logging


class NewsScraper(ABC):
    def __init__(self, name, url, logger: logging.Logger = None):
        self.name = name
        self.url = url
        self.logger = logger or logging.getLogger("scraper")

    @abstractmethod
    def scrape(self):
        """It must be implemented in each scrapper"""
        pass

    def log(self, message, level="info"):
        if self.logger:
            getattr(self.logger, level)(f"[{self.name}]{message}")
