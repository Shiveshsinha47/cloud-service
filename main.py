print("THIS IS NEW VERSION 126")

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from jose import jwt, JWTError
from database import engine, Base, SessionLocal
from models import User, File as FileModel
from auth import hash_password, verify_password, create_access_token
from storage import upload_file as upload_to_minio, minio_client, BUCKET_NAME
from cache import clear_user_cache
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# ==========================
# CORS
# ==========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"


# ==========================
# DB Dependency
# ==========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================
# Get Current User
# ==========================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# ==========================
# Register
# ==========================

@app.post("/register")
def register(email: str, password: str, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=email,
        password=hash_password(password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User created successfully"}


# ==========================
# Login
# ==========================

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.email})

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ==========================
# Upload File
# ==========================

@app.post("/upload/")
async def upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    upload_to_minio(file)

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    file_meta = FileModel(
        filename=file.filename,
        size=size,
        owner_id=current_user.id,
        is_deleted=False
    )

    db.add(file_meta)
    db.commit()
    db.refresh(file_meta)

    clear_user_cache(current_user.id)

    return {"message": "File uploaded successfully"}


# ==========================
# My Files
# ==========================

@app.get("/my-files")
def list_my_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    files = db.query(FileModel).filter(
        FileModel.owner_id == current_user.id,
        FileModel.is_deleted == False
    ).all()

    return {"files": files}


# ==========================
# Recent Files
# ==========================

@app.get("/recent")
def recent_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    files = db.query(FileModel).filter(
        FileModel.owner_id == current_user.id,
        FileModel.is_deleted == False
    ).order_by(desc(FileModel.upload_time)).limit(10).all()

    return {"files": files}


# ==========================
# Trash
# ==========================

@app.get("/trash")
def trash_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    files = db.query(FileModel).filter(
        FileModel.owner_id == current_user.id,
        FileModel.is_deleted == True
    ).all()

    return {"files": files}


# ==========================
# Restore File
# ==========================

@app.post("/restore/{filename}")
def restore_file(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    file = db.query(FileModel).filter(
        FileModel.filename == filename,
        FileModel.owner_id == current_user.id
    ).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    file.is_deleted = False
    db.commit()

    return {"message": "File restored"}


# ==========================
# Move to Trash
# ==========================

@app.delete("/delete/{filename}")
def delete_file(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    file = db.query(FileModel).filter(
        FileModel.filename == filename,
        FileModel.owner_id == current_user.id
    ).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    file.is_deleted = True
    db.commit()

    return {"message": "Moved to trash"}


# ==========================
# Download
# ==========================

@app.get("/download/{filename}")
def download_file(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    file = db.query(FileModel).filter(
        FileModel.filename == filename,
        FileModel.owner_id == current_user.id
    ).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    response = minio_client.get_object(BUCKET_NAME, filename)

    return StreamingResponse(
        response,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==========================
# Preview
# ==========================

@app.get("/preview/{filename}")
def preview_file(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    file = db.query(FileModel).filter(
        FileModel.filename == filename,
        FileModel.owner_id == current_user.id
    ).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    response = minio_client.get_object(BUCKET_NAME, filename)

    return StreamingResponse(
        response,
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


# ==========================
# Search
# ==========================

@app.get("/search")
def search_files(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    files = db.query(FileModel).filter(
        FileModel.owner_id == current_user.id,
        FileModel.filename.contains(q),
        FileModel.is_deleted == False
    ).all()

    return {"files": files}


# ==========================
# Storage Usage
# ==========================

@app.get("/storage")
def storage_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    files = db.query(FileModel).filter(
        FileModel.owner_id == current_user.id
    ).all()

    total = sum(f.size for f in files)

    return {
        "used": total,
        "limit": 1000000000
    }


# ==========================
# Share File
# ==========================

@app.get("/share/{filename}")
def share_file(filename: str):

    token = create_access_token({"file": filename})

    return {
        "share_link": f"http://localhost:8000/shared/{token}"
    }


@app.get("/shared/{token}")
def shared_file(token: str):

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    filename = payload.get("file")

    response = minio_client.get_object(BUCKET_NAME, filename)

    return StreamingResponse(response)