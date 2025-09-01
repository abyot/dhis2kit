"""DataSet model."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from .organisation import OrganisationUnit


class DataSet(BaseModel):
    """DHIS2 DataSet."""

    id: str
    displayName: str
    periodType: Optional[str] = None
    organisationUnits: Optional[List[OrganisationUnit]] = None
    dataElements: Optional[List[str]] = None
    model_config = ConfigDict(from_attributes=True)
