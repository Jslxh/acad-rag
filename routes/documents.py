from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from services.document_service import list_documents, upload_document, delete_document

documents_bp = Blueprint("documents", __name__, url_prefix="/documents")

# ---------- PAGE ----------
@documents_bp.route("/", methods=["GET"])
def documents_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("documents.html", username=session.get("username"))

# ---------- API: LIST ----------
@documents_bp.route("/list", methods=["GET"])
def list_docs_api():
    if "user_id" not in session:
        return jsonify([])

    user_id = session["user_id"]
    return jsonify(list_documents(user_id))

# ---------- API: UPLOAD ----------
@documents_bp.route("/upload", methods=["POST"])
def upload_doc_api():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        upload_document(file, session["user_id"])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------- API: DELETE ----------
@documents_bp.route("/delete/<doc_id>", methods=["POST"])
def delete_doc_api(doc_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    delete_document(doc_id, session["user_id"])
    return jsonify({"success": True})
