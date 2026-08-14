#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K2 中文字卡 — MiniMax 批量生圖
- API key 由本機檔案 .minimax_key 讀取（或環境變數 MINIMAX_API_KEY），唔會 print 出嚟。
- 生成 37 張圖，存做 img/01.jpg … img/37.jpg（app 會自動 png/jpg/webp 揀到用）。
- 已經有嘅圖會跳過（重跑唔會嘥 token）。
用法：  python3 gen_cards.py
"""
import os, sys, json, time, base64, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "img")
KEY_FILE = os.path.join(HERE, ".minimax_key")
# 國內版（minimaxi.com）；國際版係 api.minimax.io。可用環境變數 MINIMAX_URL 覆蓋。
API_URL = os.environ.get("MINIMAX_URL", "https://api.minimaxi.com/v1/image_generation")

STYLE = ("A bright, colourful, realistic and true-to-life picture of {subj}, "
         "high quality, clear and recognisable, single subject centered on a clean simple "
         "plain light background, natural lifelike appearance with rich vibrant colours, "
         "suitable as a learning flashcard for young kids. "
         "IMPORTANT: this is a REALISTIC depiction, NOT a cartoon character; do NOT add any "
         "eyes, face, smile or human features to objects, food, sun, moon, plants or animals' surroundings. "
         "No text, no letters, no numbers, no words, no watermark.")

# (檔案序號, 中文字, 圖畫主體)
CARDS = [
    # 動作（東方小朋友做動作）
    ("01","坐","an East Asian Chinese young child sitting on a small wooden chair, full body, realistic"),
    ("02","走","an East Asian Chinese young child walking, full body, side view, realistic"),
    ("03","跑","an East Asian Chinese young child running happily, full body, realistic"),
    ("04","跳","an East Asian Chinese young child jumping up in the air with joy, full body, realistic"),
    ("05","吃","an East Asian Chinese young child eating food from a bowl with a spoon, realistic"),
    ("06","喝","an East Asian Chinese young child drinking water from a cup, realistic"),
    ("07","看","an East Asian Chinese young child looking through a pair of binoculars, realistic"),
    ("08","聽","an East Asian Chinese young child listening with one hand cupped behind the ear, realistic"),
    ("09","穿","an East Asian Chinese young child putting on a t-shirt, getting dressed, realistic"),
    ("10","用","an East Asian Chinese young child using chopsticks to eat from a bowl, close up on the hand and chopsticks, realistic"),
    ("11","有","an East Asian Chinese young child happily holding up a teddy bear with both hands, showing it, realistic"),
    ("12","會","an East Asian Chinese young child giving a big thumbs up with a proud confident smile, realistic"),
    ("13","愛","an East Asian Chinese young child warmly hugging their mother, both smiling with love, realistic"),
    ("14","玩","an East Asian Chinese young child playing happily with colourful building blocks, realistic"),
    ("15","唱","an East Asian Chinese young child singing into a microphone with mouth open, realistic"),
    # 動物
    ("16","狗","a cute realistic dog"),
    ("17","貓","a cute realistic cat"),
    ("18","魚","a single colourful realistic fish"),
    ("19","鳥","a cute realistic small bird"),
    ("20","牛","a realistic cow standing"),
    ("21","羊","a realistic fluffy white sheep"),
    ("22","馬","a realistic brown horse"),
    # 食物
    ("23","飯","a bowl of white steamed rice"),
    ("24","麵","a bowl of noodles"),
    ("25","蛋","a fried egg on a plate"),
    ("26","肉","a piece of cooked meat on a plate"),
    ("27","菜","fresh green leafy vegetables, bok choy"),
    ("28","瓜","a whole green watermelon"),
    # 物件
    ("29","車","a bright colourful car"),
    ("30","書","a children's storybook, a single closed hardcover book with a colourful cover standing upright, clearly recognisable as a book"),
    ("31","球","a colourful ball"),
    ("32","門","a single wooden door"),
    ("33","家","a cute small house, a home"),
    ("34","田","a green rice paddy field"),
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

def _api_post(key, payload):
    # key 放喺臨時 curl config 檔（-K），唔會出現喺程序參數
    cfg = tempfile.NamedTemporaryFile("w", suffix=".curlcfg", delete=False, encoding="utf-8")
    try:
        cfg.write('header = "Authorization: Bearer %s"\n' % key)
        cfg.write('header = "Content-Type: application/json"\n')
        cfg.close(); os.chmod(cfg.name, 0o600)
        p = subprocess.run(
            ["curl", "-sS", "-K", cfg.name, "-X", "POST", API_URL, "--data-binary", "@-"],
            input=json.dumps(payload).encode("utf-8"),
            capture_output=True, timeout=180)
    finally:
        try: os.unlink(cfg.name)
        except OSError: pass
    if p.returncode != 0:
        raise RuntimeError("curl %d: %s" % (p.returncode, (p.stderr or b"").decode()[:200]))
    return json.loads(p.stdout.decode("utf-8"))

def _download(url):
    fd, tmp = tempfile.mkstemp(suffix=".img"); os.close(fd)
    p = subprocess.run(["curl", "-sS", "-L", "-o", tmp, url], capture_output=True, timeout=180)
    if p.returncode != 0:
        raise RuntimeError("下載失敗 curl %d: %s" % (p.returncode, (p.stderr or b"").decode()[:200]))
    with open(tmp, "rb") as f: head = f.read(16)
    if head[:3] == b"\xff\xd8\xff": ext = "jpg"
    elif head[:8] == b"\x89PNG\r\n\x1a\n": ext = "png"
    elif head[:4] == b"RIFF" and head[8:12] == b"WEBP": ext = "webp"
    else: ext = "jpg"
    return tmp, ext

def fetch_and_save(key, num, subj):
    res = _api_post(key, {
        "model": "image-01",
        "prompt": STYLE.format(subj=subj),
        "aspect_ratio": "1:1",
        "response_format": "url",
        "n": 1,
        "prompt_optimizer": True,
    })
    br = res.get("base_resp", {}) or {}
    if br.get("status_code", 0) not in (0, None):
        raise RuntimeError("API " + str(br.get("status_code")) + ": " + str(br.get("status_msg")))
    data = res.get("data") or {}
    urls = data.get("image_urls") or []
    b64s = data.get("image_base64") or []
    if urls:
        tmp, ext = _download(urls[0])
        path = os.path.join(IMG_DIR, num + "." + ext)
        os.replace(tmp, path)
    elif b64s:
        raw = base64.b64decode(b64s[0])
        path = os.path.join(IMG_DIR, num + ".jpg")
        with open(path, "wb") as f: f.write(raw)
    else:
        raise RuntimeError("冇圖回應：" + json.dumps(res, ensure_ascii=False)[:200])
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
            path = fetch_and_save(key, num, subj)
            print(f"  {num} {char}  ✓  {os.path.basename(path)}")
            done += 1
            time.sleep(1.5)   # 溫和啲，避免撞 rate limit
        except Exception as e:
            print(f"  {num} {char}  ✗  {e}")
            fail += 1
    print(f"\n完成：新生成 {done}、跳過 {skip}、失敗 {fail}。")
    if fail:
        print("失敗嘅可以再跑一次 python3 gen_cards.py（成功嗰啲會自動跳過）。")

if __name__ == "__main__":
    main()
