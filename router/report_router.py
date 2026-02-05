from typing import Optional, List
from fastapi import APIRouter, HTTPException, status,Depends,Response,Query
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.report import ReportRead, ReportCreate, ReportUpdate, ReportPatch
from models import User, Region, CrimeType, Report
from sqlalchemy.orm import joinedload
from sqlalchemy import desc, or_
from services.ai_crime_classifier import classify_crime_type

router = APIRouter(prefix="/api/reports", tags=["Reports"])

# 1. 제보 목록 (필터링/페이징)
@router.get("", response_model=List[ReportRead])
async def get_reports(
        region_id: Optional[int] = Query(None),
        crime_type_id: Optional[int] = Query(None),
        skip: int = 0,
        limit: int = 10,
        keyword: Optional[str] = Query(None, description="검색 키워드(제목/내용)"),
        sort_by: str = Query("latest", description="정렬 기준: latest(최신순), oldest(오래된순)"),
        db: Session = Depends(get_db)
):
    # 1. 쿼리 시작 (joinedload를 통해 연관 테이블을 미리 로드)
    query = db.query(Report).options(
        joinedload(Report.region),
        joinedload(Report.crime_type)
    )
    # 2. 필터링
    if region_id:
        query = query.filter(Report.region_id == region_id)
    if crime_type_id:
        query = query.filter(Report.crime_type_id == crime_type_id)

    # 2. 키워드 검색 (제목 또는 내용에 포함된 경우)
    if keyword:
            search_filter = or_(
                Report.title.contains(keyword),
                Report.content.contains(keyword)
            )
            query = query.filter(search_filter)


    # 3. 정렬 및 페이지네이션
    if sort_by == "latest":
        query = query.order_by(desc(Report.created_at))
    else:
        query = query.order_by(Report.created_at.asc())

    reports = query.offset(skip).limit(limit).all()
    return reports

# 2. 제보 단건
@router.get("/{report_id}", response_model=ReportRead)
async def get_report(
    report_id: int,
     db: Session = Depends(get_db)):
    try:
        report = db.query(Report) \
            .options(joinedload(Report.user), joinedload(Report.region)) \
            .filter(Report.id == report_id) \
            .first()
        return report
    except HTTPException:
        raise
    except Exception as e:
       print(f"Service Error: {e}")
       raise HTTPException(status_code=500, detail="Internal Server Error")

# 3. 제보 작성
@router.post("", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def create_report(
        report_data: ReportCreate,
        db: Session = Depends(get_db)
):
    # 1. (선택사항) foreign key 객체들이 실제로 존재하는지 체크하면 더 안전합니다.
    # region = db.query(Region).filter(Region.id == report_data.region_id).first()
    # if not region: raise HTTPException(status_code=400, detail="Invalid region_id")

    # AI가 content를 분석하여 crime_type_id 덮어쓰기
    ai_crime_type_id = classify_crime_type(db, report_data.content)
    if ai_crime_type_id is not None:
        report_data.crime_type_id = ai_crime_type_id

    new_report = Report(**report_data.model_dump())
    try:
        # 3. DB에 저장
        db.add(new_report)
        db.commit()  # DB에 반영
        db.refresh(new_report)  # 생성된 ID나 created_at 등을 다시 불러오기
        return new_report
    except Exception as e:
        db.rollback()  # 에러 발생 시 되돌리기
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"제보 저장 중 오류가 발생했습니다: {str(e)}"
        )

# 4. 제보 수정 - put 전체 수정
@router.put("/{report_id}", response_model=ReportRead)
async def update_report(
        report_id: int,
        update_data: ReportUpdate,
        db: Session = Depends(get_db)
):
    # 1. 수정할 기존 제보가 있는지 먼저 확인
    db_report = db.query(Report).filter(Report.id == report_id).first()

    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {report_id}에 해당하는 제보를 찾을 수 없습니다."
        )

    # 2. 데이터 업데이트
    # model_dump()를 사용해 딕셔너리로 변환 후 반복문으로 값을 교체합니다.
    update_dict = update_data.model_dump()
    for key, value in update_dict.items():
        setattr(db_report, key, value)

    try:
        # 3. DB 반영
        db.commit()
        db.refresh(db_report)
        return db_report

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수정 중 오류가 발생했습니다."
        )

# 4. 제보 수정 - patch 일부 수정
@router.patch("/{report_id}", response_model=ReportRead)
async def patch_report(
        report_id: int,
        patch_data: ReportPatch,
        db: Session = Depends(get_db)
):
    # 1. 기존 데이터 조회
    db_report = db.query(Report).filter(Report.id == report_id).first()

    if not db_report:
        raise HTTPException(status_code=404, detail="제보를 찾을 수 없습니다.")

    # 2. 실제로 전송된 데이터만 추출 (None으로 설정된 값은 제외)
    # exclude_unset=True: 클라이언트가 명시적으로 보낸 필드만 딕셔너리에 포함됨
    update_data = patch_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_report, key, value)
    try:
        db.commit()
        db.refresh(db_report)
        return db_report
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="부분 수정 중 오류 발생")

# 5. 제보 삭제
@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
        report_id: int,
        db: Session = Depends(get_db)
):
    # 1. 삭제할 데이터가 존재하는지 먼저 확인
    db_report = db.query(Report).filter(Report.id == report_id).first()

    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {report_id}에 해당하는 제보를 찾을 수 없어 삭제가 불가능합니다."
        )
    try:
        # 2. 데이터 삭제 실행
        db.delete(db_report)
        db.commit()
        # 3. 204 No Content 응답 (삭제 성공 시 보통 본문을 비워서 보냅니다)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"삭제 중 오류가 발생했습니다: {str(e)}"
        )
