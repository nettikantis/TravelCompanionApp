from datetime import datetime
from app import db


class Bookmark(db.Model):
    __tablename__ = "bookmarks"

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(120))
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    external_id = db.Column(db.String(120))  # e.g., Foursquare place id
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "city": self.city,
            "name": self.name,
            "category": self.category,
            "lat": self.lat,
            "lon": self.lon,
            "external_id": self.external_id,
            "created_at": self.created_at.isoformat(),
        }