from sqlalchemy.orm import Session

from models import Region, CrimeType
from models.officialstat import OfficialStat
from sqlalchemy import func


def fetch_official_stats(db:Session,province: str, city: str, year:int =None):
    region = db.query(Region).filter(Region.province == province, Region.city == city).first()
    if not region:
        return None

    if year is None:
        year = db.query(func.max(OfficialStat.year)).scalar() or 2024

    stats = db.query(OfficialStat).join(CrimeType).filter(
        OfficialStat.region_id == region.id,
        OfficialStat.year == year,
    ).all()

    return {
        "region": region.full_name,
        "year": year,
        "last_updated": stats[0].last_updated if stats else None,
        "statistics": [
            {"crime_major": s.crime_type.major, "crime_minor":s.crime_type.minor, "count":s.count}
            for s in stats
            #push
        ]
    }
