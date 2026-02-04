from sqlalchemy.orm import Session

from models import Region, CrimeType
from models.officialstat import OfficialStat


def fetch_official_stats(db: Session, province: str, city: str, major: str = None, minor: str = None, year: int = None):
    search_full_name = f"{province} {city}"

    query = (
        db.query(OfficialStat)
        .join(Region, OfficialStat.region_id == Region.id)
        .outerjoin(CrimeType, OfficialStat.crime_type_id == CrimeType.id)
        .filter(Region.full_name == search_full_name)
    )

    if year is None:
        from sqlalchemy import func
        year = db.query(func.max(OfficialStat.year)) \
            .join(Region) \
            .filter(Region.full_name == search_full_name).scalar()

    query = query.filter(OfficialStat.year == year)

    if major:
        query = query.filter(CrimeType.major == major)
    if minor:
        query = query.filter(CrimeType.minor == minor)

    results = query.all()

    if not results:
        return None

    return {
        "region": search_full_name,
        "year": year,
        "last_updated": results[0].last_updated,
        "statistics": [
            {
                "crime_major": res.crime_type.major if res.crime_type else "미분류",
                "crime_minor": res.crime_type.minor if res.crime_type else "미분류",
                "count": res.count
            }
            for res in results
        ]
    }