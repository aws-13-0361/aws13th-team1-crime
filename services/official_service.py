from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Region, CrimeType
from models.officialstat import OfficialStat

def fetch_official_stats(db: Session, province: str, city: str, major: str = None, minor: str = None, year: int = None):
    search_full_name = f"{province} {city}" if city else province

    query = (
        db.query(OfficialStat)
        .join(Region, OfficialStat.region_id == Region.id)
        .outerjoin(CrimeType, OfficialStat.crime_type_id == CrimeType.id)
        .filter(Region.full_name == search_full_name)
    )

    if year is None:
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

def fetch_regions(db: Session,province: str=None):
    query = db.query(Region)

    #province(시/도)가 필터가 있으면 적용한다. (Where province = "")
    if province:
        query = query.filter(Region.province == province)
        #해당 시/도 내에서는 구/군 순으로 정렬
        query = query.order_by(Region.city)
    else:
        query = query.order_by(Region.full_name)

    return query.all()

def fetch_crime_types(db:Session, major:str = None):
    if major is None:
        #대분류 목록만 중복 없이 가져오기
        results = db.query(CrimeType.major).distinct().order_by(CrimeType.major).all()
        return [{"major":r.major} for r in results]
    else:
        return db.query(CrimeType)\
                .filter(CrimeType.major == major)\
                .filter(CrimeType.major.isnot(None))\
                .order_by(CrimeType.minor).all()