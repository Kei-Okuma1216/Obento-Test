from typing import Annotated

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse

app = FastAPI()

# Request Files
# https://fastapi.tiangolo.com/ja/tutorial/request-files/#multiple-file-uploads

# 1
@app.post("/files/")
async def create_files(files: Annotated[list[bytes], File()]):
    return {
        "file_sizes": [len(file) for file in files]}

# 2
@app.post("/uploadfiles/")
async def create_upload_files(files: list[UploadFile]):
    return {
        "filenames": [file.filename for file in files]}

@app.get("/")
async def main():
    content = """
<body>
<!-- 1 -->
 <form action="/files/" enctype="multipart/form-data" method="post">
  <input name="files" type="file" multiple>
  <input type="submit">
 </form>
 <!-- 2 -->
 <form action="/uploadfiles/" enctype="multipart/form-data" method="post">
  <input name="files" type="file" multiple>
  <input type="submit">
 </form>
</body>
    """
    return HTMLResponse(content=content)