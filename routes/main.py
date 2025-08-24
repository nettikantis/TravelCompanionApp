from flask import Blueprint, render_template, request


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    q = request.args.get("q", "")
    return render_template("index.html", q=q)

