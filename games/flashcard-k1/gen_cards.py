#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K1 中文字卡 — MiniMax 批量生圖
- API key 由本機檔案 .minimax_key 讀取（或環境變數 MINIMAX_API_KEY），唔會 print 出嚟。
- 生成 37 張圖，存做 img/01.jpg … img/37.jpg（app 會自動 png/jpg/webp 揀到用）。
- 已經有嘅圖會跳過（重跑唔會嘥 token）。
用法：  python3 gen_cards.py
"""
import os, sys, json, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "img")
KEY_FILE = os.path.join(HERE, ".minimax_key")
API_URL = os.environ.get("MINIMAX_URL", "https://api.minimax.io/v1/image_generation")

STYLE = ("Cute simple cartoon illustration for a preschool flashcard, {subj}, "
         "single clear subject, centered, plain soft pastel background, thick clean "
         "outlines, bright kid-friendly colours, no text, no letters, no words.")

# (檔案序號, 中文字, 圖畫主體)
CARDS = [
    ("01","一","one single big red apple"),
    ("02","二","two yellow rubber ducks"),
    ("03","三","three red apples in a row"),
    ("04","四","four colourful balloons"),
    ("05","五","five yellow stars"),
    ("06","六","six little orange fish"),
    ("07","七","seven pink flowers"),
    ("08","八","eight purple grapes"),
    ("09","九","nine round colourful candies"),
    ("10","十","ten coloured pencils in a row"),
    ("11","口","a smiling child's open mouth"),
    ("12","手","a child's open hand waving hello"),
    ("13","耳","a single cute cartoon ear"),
    ("14","目","one big friendly cartoon eye"),
    ("15","心","a single red love heart"),
    ("16","足","a child's cute bare foot"),
    ("17","日","a bright smiling sun"),
    ("18","月","a crescent moon in a night sky with a few stars"),
    ("19","山","a green mountain with a peak"),
    ("20","水","a clear glass of water with a big water drop"),
    ("21","火","a small friendly campfire flame"),
    ("22","木","a single green tree"),
    ("23","石","a smooth grey rock stone"),
    ("24","天","a blue sky with fluffy white clouds"),
    ("25","雨","a rain cloud with blue raindrops"),
    ("26","花","a single pink flower"),
    ("27","草","a patch of green grass"),
    ("28","人","a cute cartoon child standing, front view"),
    ("29","大","a big grey elephant"),
    ("30","小","a tiny cute grey mouse"),
    ("31","上","a bird flying up high with an upward arrow"),
    ("32","下","a ball falling down with a downward arrow"),
    ("33","中","a target bullseye with an object in the centre"),
    ("34","爸","a friendly cartoon dad, father, front view"),
    ("35","媽","a friendly cartoon mum, mother, front view"),
    ("36","哥","a cartoon older brother, a bigger boy"),
    ("37","姐","a cartoon older sister, a bigger girl"),
]

def load_key():
    k = os.environ.get("MINIMAX_API_KEY", "").strip()
    if not k and os.path.exists(KEY_FILE):
        with open(KEY_FILE, encoding="utf-8") as f:
            k = f.read().strip()
    if not k or k.startswith("PUT_YOUR"):
        sys.exit("❌ 搵唔到 API key。請將你嘅 key 貼入檔案：" + KEY_FILE)
    return k

def existing(num):
    for ext in ("jpg","jpeg","png","webp"):
        p = os.path.join(IMG_DIR, num + "." + ext)
        if os.path.exists(p):
            return p
    return None

def generate(key, subj):
    body = json.dumps({
        "model": "image-01",
        "prompt": STYLE.format(subj=subj),
        "aspect_ratio": "1:1",
        "response_format": "url",
        "n": 1,
        "prompt_optimizer": True,
    }).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + key,
    })
    with urllib.request.urlopen(req, timeout=120) as r:
        res = json.loads(r.read().decode("utf-8"))
    br = res.get("base_resp", {})
    if br.get("status_code", 0) not in (0, None):
        raise RuntimeError("API: " + str(br.get("status_msg")))
    urls = (res.get("data") or {}).get("image_urls") or []
    if not urls:
        raise RuntimeError("冇 image_urls；回應：" + json.dumps(res)[:200])
    return urls[0]

def download(url, num):
    with urllib.request.urlopen(url, timeout=120) as r:
        ct = (r.headers.get("Content-Type") or "").lower()
        data = r.read()
    ext = "png" if "png" in ct else ("webp" if "webp" in ct else "jpg")
    path = os.path.join(IMG_DIR, num + "." + ext)
    with open(path, "wb") as f:
        f.write(data)
    return path

def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    key = load_key()
    done = skip = fail = 0
    for num, char, subj in CARDS:
        if existing(num):
            print(f"  {num} {char}  ⏭  已有，跳過")
            skip += 1
            continue
        try:
            url = generate(key, subj)
            path = download(url, num)
            print(f"  {num} {char}  ✓  {os.path.basename(path)}")
            done += 1
            time.sleep(1.5)   # 溫和啲，避免撞 rate limit
        except urllib.error.HTTPError as e:
            print(f"  {num} {char}  ✗  HTTP {e.code} {e.read()[:120]!r}")
            fail += 1
        except Exception as e:
            print(f"  {num} {char}  ✗  {e}")
            fail += 1
    print(f"\n完成：新生成 {done}、跳過 {skip}、失敗 {fail}。")
    if fail:
        print("失敗嘅可以再跑一次 python3 gen_cards.py（成功嗰啲會自動跳過）。")

if __name__ == "__main__":
    main()
