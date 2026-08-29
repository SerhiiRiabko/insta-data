"""Countries — static list backing the country selector (admin + site).

Deliberately not a Mongo-backed CRUD collection like `stores`: there are only
two countries right now and adding a new one is a real engineering effort
(new scrapers, store data) each time, not a self-serve admin task - a plain
constant is enough and avoids a collection nobody but this one endpoint reads.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/countries", tags=["countries"])

COUNTRIES = [
    {
        "code": "ME",
        "flag": "🇲🇪",
        "name": {
            "ukr": "Чорногорія",
            "rus": "Черногория",
            "mne": "Crna Gora",
            "srb": "Crna Gora",
            "bos": "Crna Gora",
            "eng": "Montenegro",
        },
    },
    {
        "code": "UA",
        "flag": "🇺🇦",
        "name": {
            "ukr": "Україна",
            "rus": "Украина",
            "mne": "Ukrajina",
            "srb": "Ukrajina",
            "bos": "Ukrajina",
            "eng": "Ukraine",
        },
    },
]


@router.get("")
async def list_countries():
    return {"countries": COUNTRIES}
