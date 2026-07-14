from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.db.models.checks import CheckProgram
from app.db.session import get_db
from app.schemas.check import CheckListItem, CheckResponse
from app.services.checks import CheckService
from app.utils.auth import Role, require_roles


router = APIRouter(prefix="/checks", tags=["checks"])


@router.post("", response_model=CheckResponse, status_code=status.HTTP_201_CREATED)
async def create_check(
    background_tasks: BackgroundTasks,
    program: CheckProgram = Form(...),
    files: list[UploadFile] = File(...),
    _: Role = Depends(require_roles(Role.admin, Role.specialist)),
    db: Session = Depends(get_db),
) -> CheckResponse:
    service = CheckService(db)
    return await service.create_check(program, files, background_tasks)


@router.get("", response_model=list[CheckListItem])
def list_checks(
    _: Role = Depends(require_roles(Role.admin, Role.specialist, Role.user)),
    db: Session = Depends(get_db),
) -> list[CheckListItem]:
    service = CheckService(db)
    return service.list_checks()


@router.get("/{check_id}", response_model=CheckResponse)
def get_check(
    check_id: UUID,
    _: Role = Depends(require_roles(Role.admin, Role.specialist, Role.user)),
    db: Session = Depends(get_db),
) -> CheckResponse:
    service = CheckService(db)
    return service.get_check(check_id)
