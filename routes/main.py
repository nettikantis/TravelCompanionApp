from flask import Blueprint, render_template
from models import Bookmark


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    bookmarks = Bookmark.query.order_by(Bookmark.created_at.desc()).limit(10).all()
    return render_template("index.html", bookmarks=bookmarks)