from typing import Dict

import uvicorn
from fastapi import FastAPI, HTTPException, Response, status

app = FastAPI()

db_starred_repos: Dict[str, bool] = {}


def _repo_key(owner: str, repo: str) -> str:
    return f"{owner}/{repo}"


@app.get("/user/starred/{owner}/{repo}", status_code=status.HTTP_204_NO_CONTENT)
def check_starred(owner: str, repo: str) -> Response:
    key = _repo_key(owner, repo)
    if key not in db_starred_repos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.put("/user/starred/{owner}/{repo}", status_code=status.HTTP_204_NO_CONTENT)
def star_repo(owner: str, repo: str) -> Response:
    db_starred_repos[_repo_key(owner, repo)] = True
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.delete("/user/starred/{owner}/{repo}", status_code=status.HTTP_204_NO_CONTENT)
def unstar_repo(owner: str, repo: str) -> Response:
    db_starred_repos.pop(_repo_key(owner, repo), None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/_internal/state")
def get_internal_state() -> dict[str, list[str]]:
    return {"starred": list(db_starred_repos.keys())}


if __name__ == "__main__":
    print("Fake GitHub City is online. Awaiting traffic...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
