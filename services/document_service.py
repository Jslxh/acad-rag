import os, json, uuid
from werkzeug.utils import secure_filename
from acad_rag import ingest_pdf

BASE = "data/users"

def _user_base(uid):
    base = os.path.join(BASE, str(uid))
    os.makedirs(base, exist_ok=True)
    return base

def _docs_dir(uid):
    d = os.path.join(_user_base(uid), "docs")
    os.makedirs(d, exist_ok=True)
    return d

def _registry(uid):
    return os.path.join(_user_base(uid), "documents.json")

def list_documents(uid):
    path = _registry(uid)
    if not os.path.exists(path):
        return []
    return json.load(open(path))

def upload_document(file, uid):
    docs = list_documents(uid)
    doc_id = str(uuid.uuid4())

    filename = secure_filename(file.filename)
    save_path = os.path.join(_docs_dir(uid), f"{doc_id}_{filename}")
    file.save(save_path)

    ingest_pdf(save_path, uid)

    docs.append({"id":doc_id, "filename":filename})
    json.dump(docs, open(_registry(uid),"w"), indent=2)

def delete_document(doc_id, uid):
    docs = list_documents(uid)
    new = []
    for d in docs:
        if d["id"] == doc_id:
            for f in os.listdir(_docs_dir(uid)):
                if f.startswith(doc_id):
                    os.remove(os.path.join(_docs_dir(uid), f))
        else:
            new.append(d)
    json.dump(new, open(_registry(uid),"w"), indent=2)
