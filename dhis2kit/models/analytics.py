"""Analytics response models."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class AnalyticsMetadata(BaseModel):
    """Simplified analytics metadata mapping."""

    name: Optional[str] = None
    dimension: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = None
    model_config = ConfigDict(from_attributes=True)


class AnalyticsResponse(BaseModel):
    """A flexible representation of DHIS2 analytics JSON."""

    headers: List[Dict[str, Any]]
    metaData: Dict[str, Any]
    rows: List[List[Any]]
    title: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)
