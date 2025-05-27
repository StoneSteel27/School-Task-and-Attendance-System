import asyncio
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.models.user import User
from app.schemas.user import UserCreate
from app.crud import crud_user
from app.core.config import settings
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = (logging.getLogger(__name__))


def get_superuser_email() -> str:
    default_email = getattr(settings, "FIRST_SUPERUSER_EMAIL", None)
    if default_email:
        logger.info(f"Using default superuser email: {default_email}")
        return default_email
    return input("Enter superuser email: ")


def get_superuser_password() -> str:
    default_password = getattr(settings, "FIRST_SUPERUSER_PASSWORD", None)
    if default_password:
        logger.info("Using default superuser password (from settings).")
        return default_password
    from getpass import getpass  # For securely reading password
    return getpass("Enter superuser password: ")


def get_superuser_full_name() -> str:
    default_name = getattr(settings, "FIRST_SUPERUSER_FULL_NAME", "Admin User")
    if default_name:
        return default_name
    return input("Enter superuser full name: ")

def get_superuser_roll_number(email: str) -> str:
    default_roll_number = getattr(settings, "FIRST_SUPERUSER_ROLL_NUMBER", None)
    if default_roll_number:
        logger.info(f"Using superuser roll number from settings: {default_roll_number}")
        return default_roll_number
    generated_rn = f"ADMIN-{email.split('@')[0].upper()}"
    logger.info(f"Auto-generating roll number: {generated_rn}")
    return generated_rn


async def main() -> None:
    logger.info("Starting superuser creation process...")
    db: Session = SessionLocal()

    try:
        superuser_email = get_superuser_email()
        existing_user = crud_user.get_user_by_email(db, email=superuser_email)

        if existing_user:
            logger.info(f"User with email {superuser_email} already exists.")
            updated = False
            if not existing_user.is_superuser:
                logger.info("Promoting existing user to superuser.")
                existing_user.is_superuser = True
                updated = True
            # Check and assign roll_number if missing (for backward compatibility if script run on old data)
            if not existing_user.roll_number: # <--- ADDED CHECK FOR ROLL NUMBER
                logger.info("Existing user is missing a roll number. Assigning one.")
                existing_user.roll_number = get_superuser_roll_number(existing_user.email)
                updated = True
            if updated:
                db.add(existing_user)
                db.commit()
                logger.info("Existing user successfully updated (superuser status/roll number).")
            else:
                logger.info("User is already a superuser with a roll number. No action taken.")
            return

        # If user does not exist, create new
        superuser_password = get_superuser_password()
        superuser_full_name = get_superuser_full_name()
        superuser_roll_number = get_superuser_roll_number(superuser_email) # Get/generate roll number

        # UserCreate schema will need to be updated to accept roll_number
        # For now, let's assume UserCreate is updated. We'll do that in the Pydantic step.
        user_in = UserCreate(
            email=superuser_email,
            password=superuser_password,
            full_name=superuser_full_name,
            roll_number=superuser_roll_number, # Pass roll_number
            is_superuser=True,
            is_active=True,
            role="admin"
        )

        hashed_password = get_password_hash(user_in.password)

        logger.info(f"Creating superuser: {user_in.email} with roll number: {user_in.roll_number}")
        # crud_user.create_user will also need to handle roll_number
        created_user = crud_user.create_user(
            db=db,
            user_in=user_in, # user_in now contains roll_number
            password_hash=hashed_password
        )
        logger.info(f"Superuser {created_user.email} (Roll: {created_user.roll_number}) created successfully.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        # import traceback
        # traceback.print_exc() # For more detailed error during script dev
    finally:
        db.close()
        logger.info("Database session closed.")

if __name__ == "__main__":
    asyncio.run(main())
