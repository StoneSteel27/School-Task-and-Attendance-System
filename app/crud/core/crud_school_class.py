from sqlalchemy.orm import Session, joinedload
from app.models.core.school_class import SchoolClass
from app.schemas.core.school_class import SchoolClassCreate, SchoolClassUpdate
from app.models.auth.user import User
from app.schemas.core.school_class import SchoolClass as SchoolClassSchema
from app.schemas.core.school_class import ClassTeachingStaffDetail
from app.crud.core.crud_teacher_assignment import get_teaching_staff_for_class


def get_school_class(db: Session, class_id: int) -> SchoolClassSchema | None:  # NEW SIGNATURE
    """
    Retrieve a single school class by its ID, fully populated including students and teaching staff.
    Returns a Pydantic schema object.
    """
    db_school_class_orm = (
        db.query(SchoolClass)
        .options(joinedload(SchoolClass.students))  # Eagerly load students
        .filter(SchoolClass.id == class_id)
        .first()
    )

    if not db_school_class_orm:
        return None

    teaching_staff_dicts = get_teaching_staff_for_class(db=db, school_class=db_school_class_orm)

    teaching_staff_models = [ClassTeachingStaffDetail(**staff_dict) for staff_dict in teaching_staff_dicts]

    class_pydantic_data = SchoolClassSchema.model_validate(db_school_class_orm).model_dump()
    class_pydantic_data['teaching_staff'] = teaching_staff_models

    return SchoolClassSchema(**class_pydantic_data)

def get_school_class_by_class_code(db: Session, class_code: str) -> SchoolClassSchema | None: # NEW SIGNATURE
    """
    Retrieve a single school class by its class_code, fully populated including students and teaching staff.
    Returns a Pydantic schema object.
    """
    db_school_class_orm = (
        db.query(SchoolClass)
        .options(joinedload(SchoolClass.students))  # Eagerly load students
        .filter(SchoolClass.class_code == class_code)
        .first()
    )

    if not db_school_class_orm:
        return None

    teaching_staff_dicts = get_teaching_staff_for_class(db=db, school_class=db_school_class_orm)
    teaching_staff_models = [ClassTeachingStaffDetail(**staff_dict) for staff_dict in teaching_staff_dicts]

    # Use .model_validate and then add/replace the teaching_staff attribute.
    # This leverages Pydantic's ORM mapping for most fields and then injects our custom-fetched list.
    school_class_pydantic_obj = SchoolClassSchema.model_validate(db_school_class_orm)
    school_class_pydantic_obj.teaching_staff = teaching_staff_models # Directly set the pydantic attribute

    return school_class_pydantic_obj


def get_school_classes(
        db: Session, skip: int = 0, limit: int = 100
) -> list[SchoolClassSchema]:  # MODIFIED return type
    """
    Retrieve a list of school classes with pagination.
    Each class will include students and teaching staff.
    WARNING: This can become N+1 heavy if not optimized or if teaching_staff is complex per class.
             For now, it will call get_teaching_staff_for_class for each class in the list.
    """
    school_classes_orm = db.query(SchoolClass).order_by(SchoolClass.class_code).offset(skip).limit(limit).all()

    results: list[SchoolClassSchema] = []
    for db_school_class_orm in school_classes_orm:
        teaching_staff_dicts = get_teaching_staff_for_class(db=db, school_class=db_school_class_orm)
        teaching_staff_models = [ClassTeachingStaffDetail(**staff_dict) for staff_dict in teaching_staff_dicts]
        school_class_pydantic_obj = SchoolClassSchema.model_validate(db_school_class_orm)
        school_class_pydantic_obj.teaching_staff = teaching_staff_models
        results.append(school_class_pydantic_obj)

    return results
def create_school_class(db: Session, *, class_in: SchoolClassCreate) -> SchoolClass: # Modified return
    db_class_data = class_in.model_dump()
    db_class_orm = SchoolClass(**db_class_data)
    db.add(db_class_orm)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(db_class_orm)
    # For a newly created class, students and teaching_staff will be empty.
    # SchoolClassSchema.from_orm will correctly initialize them to [] as per schema default.
    return db_class_orm


def update_school_class(
        db: Session,
        *,
        db_class: SchoolClass,  # Existing ORM instance
        class_in: SchoolClassUpdate
) -> SchoolClassSchema:  # Modified return
    update_data = class_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_class, field, value)

    db.add(db_class)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(db_class)

    # After update, we need to fetch its students and teaching staff to return the full Pydantic object
    # This is essentially what get_school_class(db, class_id=db_class.id) would do.
    return get_school_class(db, class_id=db_class.id)


def remove_school_class(db: Session, *, db_class_to_delete: SchoolClass) -> SchoolClassSchema:  # Modified return
    deleted_class_details_schema = get_school_class(db, class_id=db_class_to_delete.id)

    db.delete(db_class_to_delete)
    db.commit()

    return deleted_class_details_schema

def get_school_class_orm_by_class_code(db: Session, class_code: str) -> SchoolClass | None: # Returns ORM model
    return (
        db.query(SchoolClass)
        .filter(SchoolClass.class_code == class_code)
        .first()
    )

def get_school_class_orm_by_id(db: Session, class_id: int) -> SchoolClass | None: # Returns ORM model
    return (
        db.query(SchoolClass)
        .filter(SchoolClass.id == class_id)
        .first()
    )


# Create a simple object to provide access to all school class CRUD functions
class CRUDSchoolClass:
    """CRUD operations for SchoolClass model"""

    def get(self, db: Session, class_id: int):
        return get_school_class(db, class_id)

    def get_by_class_code(self, db: Session, class_code: str):
        return get_school_class_by_class_code(db, class_code)

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100):
        return get_school_classes(db, skip, limit)

    def create(self, db: Session, *, obj_in):
        return create_school_class(db, class_in=obj_in)

    def update(self, db: Session, *, db_obj, obj_in):
        return update_school_class(db, db_class=db_obj, class_in=obj_in)

    def remove(self, db: Session, *, db_obj):
        return remove_school_class(db, db_class_to_delete=db_obj)

    def get_orm_by_class_code(self, db: Session, class_code: str):
        return get_school_class_orm_by_class_code(db, class_code)

    def get_orm_by_id(self, db: Session, class_id: int):
        return get_school_class_orm_by_id(db, class_id)


# Create the instance that will be imported
school_class = CRUDSchoolClass()
