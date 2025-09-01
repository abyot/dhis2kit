from dhis2kit.models.analytics import AnalyticsResponse
from dhis2kit.models.dataelement import CategoryCombo, CategoryOption, DataElement
from dhis2kit.models.organisation import OrganisationUnit


def test_dataelement_min():
    de = DataElement(id="de1", displayName="DE1")
    assert de.id == "de1"
    assert de.displayName == "DE1"


def test_dataelement_nested():
    cat = CategoryOption(id="co1", displayName="Male")
    combo = CategoryCombo(id="cc1", displayName="Sex", categoryOptions=[cat])
    de = DataElement(id="de2", displayName="DE2", categoryCombo=combo)
    assert de.categoryCombo.categoryOptions[0].displayName == "Male"


def test_orgunit_tree():
    parent = OrganisationUnit(id="p1", displayName="Parent", level=1)
    child = OrganisationUnit(id="c1", displayName="Child", level=2, parent=parent)
    assert child.ancestors()[0].id == "p1"


def test_analytics_model(sample_analytics):
    ar = AnalyticsResponse(**sample_analytics)
    assert ar.rows[0][0] == "Uvn6LCg7dVU"
    assert ar.metaData["items"]["Uvn6LCg7dVU"]["name"] == "ANC 1 Coverage"
