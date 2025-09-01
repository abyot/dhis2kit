"""DataElement and related nested structures."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class CategoryOption(BaseModel):
    """A single category option (e.g., Female/Male)."""

    id: str
    displayName: str
    model_config = ConfigDict(from_attributes=True)


class CategoryCombo(BaseModel):
    """A combination of category options."""

    id: str
    displayName: str
    categoryOptions: Optional[List[CategoryOption]] = None
    model_config = ConfigDict(from_attributes=True)


class Option(BaseModel):
    """A single Option in an OptionSet."""

    id: str
    code: Optional[str] = None
    displayName: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class OptionSet(BaseModel):
    """A collection of Options."""

    id: str
    displayName: str
    valueType: Optional[str] = None
    options: Optional[List[Option]] = None
    model_config = ConfigDict(from_attributes=True)


class DataElement(BaseModel):
    """DHIS2 DataElement."""

    id: str
    displayName: str
    shortName: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    domainType: Optional[str] = None
    valueType: Optional[str] = None
    categoryCombo: Optional[CategoryCombo] = None
    optionSet: Optional[OptionSet] = None
    model_config = ConfigDict(from_attributes=True)
