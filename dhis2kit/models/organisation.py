"""OrganisationUnit model with simple tree helpers."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class OrganisationUnit(BaseModel):
    """DHIS2 OrganisationUnit with parent/children and an ancestors() helper."""

    id: str
    displayName: str
    level: Optional[int] = None
    code: Optional[str] = None
    parent: Optional[OrganisationUnit] = None
    children: Optional[List[OrganisationUnit]] = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    def ancestors(self):
        """Return ancestors from parent up to root."""
        res = []
        p = self.parent
        while p is not None:
            res.append(p)
            p = p.parent
        return res
