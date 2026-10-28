from app.core.config import get_settings
from app.ingestion.base import EventProvider, ProviderError
from app.ingestion.providers.football_data import FootballDataProvider
from app.ingestion.providers.jolpica import JolpicaProvider
from app.models.enums import DataSource


def get_provider(source: DataSource) -> EventProvider:
    match source:
        case DataSource.FOOTBALL_DATA:
            api_key = get_settings().football_data_api_key
            if not api_key:
                raise ProviderError("FOOTBALL_DATA_API_KEY is not set")
            return FootballDataProvider(api_key)
        case DataSource.JOLPICA:
            return JolpicaProvider()
