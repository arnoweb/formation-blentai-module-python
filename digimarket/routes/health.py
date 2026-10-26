from apiflask import APIBlueprint
from flask import current_app
from sqlalchemy import text

from digimarket.database import db
from digimarket.schemas import HealthOut

health_bp = APIBlueprint("health", __name__, url_prefix="/health", tag="Health")


@health_bp.get("")
@health_bp.output(HealthOut)
@health_bp.doc(summary="État de l'API et de la base de données", responses=[503])
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        current_app.logger.exception("Health check : base de données inaccessible")
        return {"status": "error", "database": "error"}, 503

    return {"status": "ok", "database": "ok"}