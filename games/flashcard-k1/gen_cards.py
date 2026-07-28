#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K1 中文字卡 — MiniMax 批量生圖
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
    ("01","一","exactly ONE single red apple, one apple only, centered, clearly one item"),
    ("02","二","exactly TWO identical red apples placed side by side, two apples only, clearly separated and easy to count"),
    ("03","三","exactly THREE identical red apples in a neat straight row, three apples only, clearly separated and easy to count"),
    ("04","四","exactly FOUR identical yellow rubber ducks in a neat straight row, four ducks only, clearly separated and easy to count"),
    ("05","五","exactly FIVE identical yellow stars in a neat straight row, five stars only, clearly separated and easy to count"),
    ("06","六","exactly SIX identical red strawberries arranged in two neat rows of three, six strawberries only, clearly separated and easy to count"),
    ("07","七","exactly SEVEN identical red apples, arranged as a top row of FOUR apples and a bottom row of THREE apples (4 plus 3 makes seven), clearly separated, exactly seven apples and no more"),
    ("08","八","exactly EIGHT identical orange oranges, arranged as a top row of FOUR oranges and a bottom row of FOUR oranges, clearly separated, exactly eight oranges, not nine"),
    ("09","九","exactly NINE identical round colourful candies arranged in three neat rows of three, nine candies only, clearly separated and easy to count"),
    ("10","十","exactly TEN identical yellow lemons, arranged as a top row of FIVE lemons and a bottom row of FIVE lemons, clearly separated, exactly ten lemons, not twelve"),
    ("11","口","a realistic close-up of an East Asian Chinese young child's mouth and lips, warm tan skin"),
    ("12","手","an East Asian Chinese young child's open hand, palm facing forward, warm tan skin, realistic"),
    ("13","耳","a realistic close-up of an East Asian Chinese young child's ear, warm tan skin"),
    ("14","目","a realistic close-up of an East Asian Chinese young child's eye with a dark brown iris"),
    ("15","心","a single simple red love-heart shape, flat and clean, no face"),
    ("16","足","an East Asian Chinese young child's bare foot, warm tan skin, realistic"),
    ("17","日","a bright shining sun in a clear blue sky, realistic, no face"),
    ("18","月","a crescent moon in a night sky with a few stars"),
    ("19","山","a green mountain with a peak"),
    ("20","水","a clear glass of water with a big water drop"),
    ("21","火","a realistic small campfire with orange flames"),
    ("22","木","a single green tree"),
    ("23","石","a smooth grey rock stone"),
    ("24","天","a blue sky with fluffy white clouds"),
    ("25","雨","a rain cloud with blue raindrops"),
    ("26","花","a single pink flower"),
    ("27","草","a patch of green grass"),
    ("28","人","an East Asian Chinese young child standing, black hair, dark eyes, warm tan skin, front view, realistic"),
    ("29","大","two balls side by side on a plain white background: one LARGE bright red glossy ball and one much smaller grey ball, the big red ball clearly much bigger, soft natural shadows"),
    ("30","小","two balls side by side on a plain white background: one LARGE grey ball and one much smaller bright red glossy ball, the small red ball clearly much smaller, soft natural shadows"),
    ("31","上","a bird flying up high with an upward arrow"),
    ("32","下","a ball falling down with a downward arrow"),
    ("33","中","a target bullseye with an object in the centre"),
    ("34","爸","an East Asian Chinese adult man, a father about 35 years old, black hair, warm friendly smile, head and shoulders portrait, front view, realistic"),
    ("35","媽","an East Asian Chinese adult woman, a mother about 35 years old, black hair, gentle warm smile, clearly a grown-up woman not a child, head and shoulders portrait, front view, realistic"),
    ("36","哥","an East Asian Chinese older brother, a boy about 8 years old, black hair, warm tan skin, friendly, head and shoulders portrait, front view, realistic"),
    ("37","姐","an East Asian Chinese older sister, a girl about 8 years old, black hair, warm tan skin, friendly, head and shoulders portrait, front view, realistic"),
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
