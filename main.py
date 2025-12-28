import urls
from fastapi import FastAPI, Request, HTTPException, status
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse



import httpx
from fastapi.templating import Jinja2Templates
import re
from typing import Optional
app = FastAPI()

templates = Jinja2Templates(directory="templates")


class Resp(BaseModel):
    url: str
    clean: Optional[int] = 0
    fix: Optional[int] = 0
    archive: Optional[int] = 0
    customReplacements: Optional[dict] = {}
    settings: Optional[dict] = {}
shortcuts = {"ios-version":1.1, "ios-link": "https://www.icloud.com/shortcuts/f813edf47f7946888be538f3f0fa553a"}


defaultReplacements = {
   "x.com": "fxtwitter.com", # https://github.com/FixTweet/FxTwitter
   "twitter.com": "fxtwitter.com",
   "instagram.com": "uuinstagram.com", # https://github.com/Wikidepia/InstaFix
   "tiktok.com": "tnktok.com", # https://github.com/okdargy/fxtiktok
   "reddit.com": "rxddit.com", # https://github.com/MinnDevelopment/fxreddit
   "facebook.com": "facebed.com", # https://github.com/facebed/facebed
   "bsky.app": "bskx.app", # https://github.com/Lexedia/VixBluesky
   "threads.net": "fixthreads.net", # https://github.com/milanmdev/fixthreads
   "tumblr.com": "tpmblr.com", # https://github.com/knuxify/fxtumblr
}

def genericParser(url, keys):
    parsedUrl = urlparse(url)
    for i in keys:
        netloc = parsedUrl.netloc
        if i in netloc:
            location = netloc.find(i)
            if location == 0 or netloc[location -1] == "." or netloc[location -1] == "/":
                o = netloc[:location] + keys[i]
                url = urlunparse(parsedUrl._replace(netloc=o))
            else: 
                pass
    
    return url


def cleanUrl(url):
    rules = urls.load_cleaning_rules("Rules/data.min.json")
    url = urls.clean_url(rules=rules, url=url)
    return url
    

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        request=request, name="superurl.html", context={"iosLink": shortcuts["ios-link"]}
    )

@app.get("/api/v0/shortcut")
async def shortcut():
    return shortcuts

@app.post("/api/v0/clean")
async def clean(resp: Resp):
    if resp.url:
        url = resp.url
    else: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL empty"
        )
    if resp.clean:
        url = cleanUrl(url)
        #https://www.reddit.com/comments/28gpzg/-/iwtv0g9/
        if re.search(r"^(https?:\/\/)?(www\.)?reddit\.com", url):
            url = re.sub(r"com\/[^>]+\/comments", "com/comments", url, 1)
            url = re.sub("comment/", "-", url, 1)
    if resp.archive:
        try:
            await httpx.get("http://web.archive.org/save/" + url, timeout=0.1)
        except Exception as ex:
            pass
    if resp.fix:
        newurl = ""
        if resp.customReplacements:
            try:
                newurl = genericParser(url, resp.customReplacements)
                if newurl != url:
                    url = newurl
                else: 
                    url = genericParser(url, defaultReplacements)
            except:
                pass
        else:
            url = genericParser(url, defaultReplacements)        
    
    return {"output": url}
            
app.mount("/", StaticFiles(directory="static"), name="static")