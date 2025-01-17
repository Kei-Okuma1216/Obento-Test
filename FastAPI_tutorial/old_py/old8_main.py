from fastapi import FastAPI, File, Form, UploadFile

app = FastAPI()

# curl -L -X POST http://127.0.0.1:8000/files/ -F file=@path/to/your/data.json -F token=your_token

@app.post("/files/")
async def create_file(
    file: bytes = File(), fileb: UploadFile = File(), token: str = Form()
):
    return {
        "file_size": len(file),
        "token": token,
        "fileb_content_type": fileb.content_type,
    }