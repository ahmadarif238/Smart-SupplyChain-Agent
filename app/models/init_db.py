from app.models.database import Base, engine
from app.models import schemas

import logging
logger = logging.getLogger("init_db")

logger.info("Creating database tables...")
Base.metadata.create_all(bind=engine)
logger.info("All tables created successfully ✅")
