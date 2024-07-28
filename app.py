from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Union
import httpx
import json

# add cors
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

JSON_SERVER_URL = "http://localhost:3000"  # Adjust this if your json-server runs on a different port

class File(BaseModel):
    name: str
    type: str = "file"

class Folder(BaseModel):
    name: str
    type: str = "folder"
    children: List[Union[File, "Folder"]] = []

Folder.model_rebuild()

class FileSystem(BaseModel):
    root: Folder

@app.get("/files")
async def get_files():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{JSON_SERVER_URL}/fileSystem")
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch file system")

@app.post("/files")
async def create_file_or_folder(item: Union[File, Folder], path: str):
    async with httpx.AsyncClient() as client:
        current_system = await client.get(f"{JSON_SERVER_URL}/fileSystem")
        file_system = FileSystem(**current_system.json())

        folders = path.split("/")
        current_folder = file_system.root
        for folder in folders:
            if folder:
                current_folder = next((f for f in current_folder.children if f.name == folder and f.type == "folder"), None)
                if not current_folder:
                    raise HTTPException(status_code=404, detail=f"Folder {folder} not found")

        current_folder.children.append(item)

        response = await client.put(f"{JSON_SERVER_URL}/fileSystem", json=file_system.dict())
        if response.status_code == 200:
            return {"message": "Item created successfully"}
        raise HTTPException(status_code=response.status_code, detail="Failed to create item")

@app.put("/files/{item_name}")
async def update_file_or_folder(item_name: str, updated_item: Union[File, Folder], path: str):
    async with httpx.AsyncClient() as client:
        current_system = await client.get(f"{JSON_SERVER_URL}/fileSystem")
        file_system = FileSystem(**current_system.json())

        folders = path.split("/")
        current_folder = file_system.root
        for folder in folders:
            if folder:
                current_folder = next((f for f in current_folder.children if f.name == folder and f.type == "folder"), None)
                if not current_folder:
                    raise HTTPException(status_code=404, detail=f"Folder {folder} not found")

        item_index = next((i for i, item in enumerate(current_folder.children) if item.name == item_name), None)
        if item_index is None:
            raise HTTPException(status_code=404, detail=f"Item {item_name} not found")

        current_folder.children[item_index] = updated_item

        response = await client.put(f"{JSON_SERVER_URL}/fileSystem", json=file_system.dict())
        if response.status_code == 200:
            return {"message": "Item updated successfully"}
        raise HTTPException(status_code=response.status_code, detail="Failed to update item")

@app.delete("/files/{item_name}")
async def delete_file_or_folder(item_name: str, path: str):
    async with httpx.AsyncClient() as client:
        current_system = await client.get(f"{JSON_SERVER_URL}/fileSystem")
        file_system = FileSystem(**current_system.json())

        folders = path.split("/")
        current_folder = file_system.root
        for folder in folders:
            if folder:
                current_folder = next((f for f in current_folder.children if f.name == folder and f.type == "folder"), None)
                if not current_folder:
                    raise HTTPException(status_code=404, detail=f"Folder {folder} not found")

        item_index = next((i for i, item in enumerate(current_folder.children) if item.name == item_name), None)
        if item_index is None:
            raise HTTPException(status_code=404, detail=f"Item {item_name} not found")

        del current_folder.children[item_index]

        response = await client.put(f"{JSON_SERVER_URL}/fileSystem", json=file_system.dict())
        if response.status_code == 200:
            return {"message": "Item deleted successfully"}
        raise HTTPException(status_code=response.status_code, detail="Failed to delete item")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)