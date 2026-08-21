#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小火車排排坐（排序遊戲）— MiniMax 批量生圖
- API key 由本機檔案 .minimax_key 讀取（或環境變數 MINIMAX_API_KEY），唔會 print 出嚟。
- 物件圖（ball/apple/star/duck/strawberry/tree）用「純白背景、單一主體」→ 前端用 mix-blend-mode:multiply 去白底、可縮放/平鋪。
- 情境圖（m1..m4 朝早流程、p1..p4 種子開花）用實景，前端 cover 裁成方形。
- 已經有嘅圖會跳過（重跑唔會嘥 token）。
用法：  python3 gen_cards.py
"""
import os, sys, json, time, base64, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "img")
KEY_FILE = os.path.join(HERE, ".minimax_key")
API_URL = os.environ.get("MINIMAX_URL", "https://api.minimaxi.com/v1/image_generation")

# 物件：一定要純白背景 + 單一主體（前端靠白底做透明效果）
STYLE_OBJ = ("A bright, colourful, realistic and true-to-life photo of {subj}, "
             "a SINGLE object centered, isolated on a PURE PLAIN WHITE background (#ffffff), "
             "soft even studio lighting, no shadow on the background, high quality, clear and recognisable, "
             "rich vibrant colours, suitable as a learning flashcard for young kids. "
             "IMPORTANT: realistic depiction, NOT a cartoon; do NOT add any eyes, face, smile or human features to the object. "
             "No text, no letters, no numbers, no words, no watermark, no border.")

# 情境：實景，東方小朋友，畫面乾淨
STYLE_SCENE = ("A bright, colourful, realistic and true-to-life picture of {subj}, "
               "clean simple uncluttered background, natural lifelike appearance with warm vibrant colours, "
               "single clear subject, suitable as a learning picture for young kids. "
               "IMPORTANT: realistic depiction, NOT a cartoon. "
               "No text, no letters, no numbers, no words, no watermark.")

# (檔名 key, 種類 obj/scene, 圖畫主體)
CARDS = [
    # ---- 物件（純白底）----
    ("ball",       "obj", "a single bright glossy red rubber ball"),
    ("apple",      "obj", "a single fresh shiny red apple with a small green leaf on top"),
    ("star",       "obj", "a single glossy golden-yellow five-pointed star ornament"),
    ("duck",       "obj", "a single cute yellow rubber duck bath toy"),
    ("strawberry", "obj", "a single fresh ripe red strawberry with small green leaves"),
    ("tree",       "obj", "a single lush round green broadleaf tree with a short brown trunk, the whole tree from base to top"),
    # ---- 朝早流程（由朝到晚）----
    ("m1", "scene", "an East Asian Chinese young child just waking up and stretching arms in bed in the morning, bright bedroom"),
    ("m2", "scene", "an East Asian Chinese young child brushing teeth with a toothbrush at a bathroom sink"),
    ("m3", "scene", "an East Asian Chinese young child sitting at a table eating breakfast with a bowl"),
    ("m4", "scene", "an East Asian Chinese young child wearing a school backpack walking to school, morning street"),
    # ---- 種子變花 ----
    ("p1", "scene", "a single brown seed lying on dark brown soil, macro close up"),
    ("p2", "scene", "a tiny green sprout with two small leaves growing out of brown soil"),
    ("p3", "scene", "a young small green leafy plant with several leaves growing in soil, not yet flowering"),
    ("p4", "scene", "one beautiful blooming flower with colourful petals on a green stem in soil"),
    # ---- 成長階段（由細到大）----
    ("g1", "scene", "a cute East Asian newborn baby lying down wrapped in a soft blanket, close up"),
    ("g2", "scene", "an East Asian Chinese young child about five years old standing and smiling, full body, plain background"),
    ("g3", "scene", "a grown-up adult East Asian Chinese woman in her thirties, clearly a fully grown tall adult with adult body proportions, standing and smiling, full body, wearing casual clothes, plain background, NOT a child"),
    ("g4", "scene", "a happy East Asian Chinese elderly grandparent with grey hair smiling, upper body, plain background"),
    # ---- 蝴蝶生命週期 ----
    ("b1", "scene", "a small cluster of tiny round butterfly eggs on a green leaf, macro close up"),
    ("b2", "scene", "a green caterpillar crawling on a green leaf, macro close up"),
    ("b3", "scene", "a green butterfly chrysalis cocoon hanging from a small twig, macro close up"),
    ("b4", "scene", "a beautiful colourful butterfly with fully open wings resting on a flower"),
    # ---- 洗手步驟 ----
    ("w1", "scene", "a young child's two hands being wet under a running water tap at a sink, close up"),
    ("w2", "scene", "a young child's two hands covered with white soap bubbles and foam, washing, close up"),
    ("w3", "scene", "a young child rubbing and scrubbing two soapy foamy hands together, close up"),
    ("w4", "scene", "a young child drying both hands with a clean towel, close up"),
    # ---- 一日天色（由朝到晚）----
    ("d1", "scene", "early morning daytime sky, a soft pale light blue sky with a small low morning sun near the horizon, fresh bright gentle morning light, calm scenery, mostly blue not orange, no people"),
    ("d2", "scene", "a bright blue clear midday sky with a shining sun over a green landscape, no people"),
    ("d3", "scene", "a beautiful sunset with orange pink and purple sky over the horizon, scenery, no people"),
    ("d4", "scene", "a calm night sky with a bright full moon and twinkling stars, dark blue evening, no people"),
]

def load_key():
    k = os.environ.get("MINIMAX_API_KEY", "").strip()
    if not k and os.path.exists(KEY_FILE):
        with open(KEY_FILE, encoding="utf-8") as f:
            k = f.read().strip()
    if not k or k.startswith("PUT_YOUR"):
        sys.exit("❌ 搵唔到 API key。請將 key 放入檔案：" + KEY_FILE)
    return k

def existing(key):
    for ext in ("jpg","jpeg","png","webp"):
        p = os.path.join(IMG_DIR, key + "." + ext)
        if os.path.exists(p):
            return p
    return None

def _api_post(key, payload):
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

def fetch_and_save(key, name, kind, subj):
    style = STYLE_OBJ if kind == "obj" else STYLE_SCENE
    res = _api_post(key, {
        "model": "image-01",
        "prompt": style.format(subj=subj),
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
        path = os.path.join(IMG_DIR, name + "." + ext)
        os.replace(tmp, path)
    elif b64s:
        raw = base64.b64decode(b64s[0])
        path = os.path.join(IMG_DIR, name + ".jpg")
        with open(path, "wb") as f: f.write(raw)
    else:
        raise RuntimeError("冇圖回應：" + json.dumps(res, ensure_ascii=False)[:200])
    return path

def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    key = load_key()
    done = skip = fail = 0
    for name, kind, subj in CARDS:
        if existing(name):
            print(f"  {name:11s} ⏭  已有，跳過")
            skip += 1
            continue
        try:
            path = fetch_and_save(key, name, kind, subj)
            print(f"  {name:11s} ✓  {os.path.basename(path)}")
            done += 1
            time.sleep(1.5)
        except Exception as e:
            print(f"  {name:11s} ✗  {e}")
            fail += 1
    print(f"\n完成：新生成 {done}、跳過 {skip}、失敗 {fail}。")
    if fail:
        print("失敗嘅可以再跑一次 python3 gen_cards.py（成功嗰啲會自動跳過）。")

if __name__ == "__main__":
    main()
