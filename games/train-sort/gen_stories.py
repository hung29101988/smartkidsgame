#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小火車排排坐 — 故事排序系列（角色一致版）
- 每個「有角色」故事：先生成一張角色參考頭像（存 img/_<story>_ref.jpg，gitignore），
  再用 MiniMax subject_reference 生每一格，確保同一故事嘅小朋友唔會變樣。
- 「自然/生命週期」故事（frog 等）冇角色，直接生。
- key 由 .minimax_key 讀取，唔會 print；已有嘅圖跳過。
用法：  python3 gen_stories.py
"""
import os, sys, json, time, base64, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "img")
KEY_FILE = os.path.join(HERE, ".minimax_key")
API_URL = os.environ.get("MINIMAX_URL", "https://api.minimaxi.com/v1/image_generation")

SCENE = ("a bright, colourful, realistic and true-to-life photo of {subj}, "
         "clean simple uncluttered background, natural lifelike appearance, warm vibrant colours, "
         "single clear subject, suitable as a learning picture for young kids. "
         "Realistic depiction, NOT a cartoon. No text, no letters, no numbers, no words, no watermark.")

REF = ("a realistic photo, clear front portrait headshot of {subj}, "
       "looking at camera, plain light grey studio background, soft even lighting. "
       "No text, no watermark.")

# 故事：char = 角色描述（None = 冇角色）；panels = [(key, 場景英文, 廣東話語音)]
STORIES = [
    {"id":"bath", "char":"a happy East Asian Chinese little girl about 5 years old, shoulder-length black hair, cheerful face",
     "panels":[
        ("bath1","a little girl wrapped in a towel standing next to a bathtub full of white bubbles, about to take a bath","準備沖涼"),
        ("bath2","a little girl sitting inside a bubble bath washing herself with soap","搽番梘沖水"),
        ("bath3","a little girl wrapped in a big fluffy towel drying herself after a bath","抹乾身"),
        ("bath4","a little girl wearing clean pyjamas, clean fresh and happy after a bath","著返睡衣"),
     ]},
    {"id":"bake", "char":"a cheerful East Asian Chinese little boy about 5 years old, short black hair, wearing an apron",
     "panels":[
        ("bake1","a little boy mixing cake batter in a big bowl with a whisk in a kitchen","攪拌粉漿"),
        ("bake2","a little boy pouring cake batter into a round cake baking pan","倒入蛋糕模"),
        ("bake3","a little boy putting a cake pan into an oven","放入焗爐"),
        ("bake4","a little boy proudly holding a finished decorated birthday cake","完成蛋糕"),
     ]},
    {"id":"doc", "char":"an East Asian Chinese little girl about 5 years old, hair in a ponytail, gentle face",
     "panels":[
        ("doc1","a little girl looking sick and tired lying on a sofa with a thermometer, feeling unwell","發燒唔舒服"),
        ("doc2","a little girl being examined by a friendly doctor using a stethoscope in a clinic","去睇醫生"),
        ("doc3","a little girl taking medicine from a spoon at home","食藥"),
        ("doc4","a healthy happy little girl smiling and playing again, all better","好返晒"),
     ]},
    {"id":"road", "char":"an East Asian Chinese little boy about 5 years old, short black hair, wearing a blue jacket",
     "panels":[
        ("road1","a little boy standing at a pedestrian crossing waiting, a red do-not-walk traffic light showing","等紅燈"),
        ("road2","a little boy at a pedestrian crossing as the green walk traffic light lights up","綠燈著咗"),
        ("road3","a little boy looking left and right carefully before crossing the road","望左望右"),
        ("road4","a little boy safely reaching the other side of a zebra crossing","安全過到馬路"),
     ]},
    {"id":"slide", "char":"a lively East Asian Chinese little girl about 5 years old, two ponytails, pink shirt",
     "panels":[
        ("slide1","a little girl waiting in line at the bottom of a colourful playground slide","排隊等玩"),
        ("slide2","a little girl climbing up the ladder steps of a playground slide","爬樓梯"),
        ("slide3","a little girl sliding down a playground slide","滑落嚟"),
        ("slide4","a little girl happily landing at the bottom of the slide","開心落地"),
     ]},
    # 生命週期：冇角色
    {"id":"frog", "char":None,
     "panels":[
        ("frog1","a cluster of jelly-like frog eggs floating in clear pond water, macro close up","青蛙蛋"),
        ("frog2","a single small black tadpole swimming in pond water","蝌蚪"),
        ("frog3","a tadpole that has grown small back legs, becoming a froglet, in water","長出後腳"),
        ("frog4","one green frog sitting on a green leaf by a pond","變青蛙"),
     ]},
]

def load_key():
    k = os.environ.get("MINIMAX_API_KEY", "").strip()
    if not k and os.path.exists(KEY_FILE):
        k = open(KEY_FILE, encoding="utf-8").read().strip()
    if not k: sys.exit("❌ 搵唔到 API key：" + KEY_FILE)
    return k

def existing(key):
    for ext in ("jpg","jpeg","png","webp"):
        p = os.path.join(IMG_DIR, key + "." + ext)
        if os.path.exists(p): return p
    return None

def _post(key, payload):
    cfg = tempfile.NamedTemporaryFile("w", suffix=".curlcfg", delete=False, encoding="utf-8")
    try:
        cfg.write('header = "Authorization: Bearer %s"\n' % key)
        cfg.write('header = "Content-Type: application/json"\n'); cfg.close(); os.chmod(cfg.name,0o600)
        p = subprocess.run(["curl","-sS","-K",cfg.name,"-X","POST",API_URL,"--data-binary","@-"],
            input=json.dumps(payload).encode("utf-8"), capture_output=True, timeout=180)
    finally:
        try: os.unlink(cfg.name)
        except OSError: pass
    if p.returncode != 0:
        raise RuntimeError("curl %d: %s" % (p.returncode,(p.stderr or b"").decode()[:200]))
    return json.loads(p.stdout.decode("utf-8"))

def _download(url, path):
    p = subprocess.run(["curl","-sS","-L","-o",path,url], capture_output=True, timeout=180)
    if p.returncode != 0: raise RuntimeError("下載失敗:"+(p.stderr or b"").decode()[:150])

def _img_url(res):
    br = res.get("base_resp",{}) or {}
    if br.get("status_code",0) not in (0,None):
        raise RuntimeError("API "+str(br.get("status_code"))+": "+str(br.get("status_msg")))
    urls = (res.get("data") or {}).get("image_urls") or []
    if not urls: raise RuntimeError("冇圖:"+json.dumps(res,ensure_ascii=False)[:150])
    return urls[0]

def get_ref_datauri(key, story):
    """攞角色參考圖 → base64 data URI（存低 _<id>_ref.jpg 重用，確保 rerun 同一塊臉）"""
    ref_path = os.path.join(IMG_DIR, "_%s_ref.jpg" % story["id"])
    if not os.path.exists(ref_path):
        res = _post(key, {"model":"image-01","prompt":REF.format(subj=story["char"]),
            "aspect_ratio":"1:1","response_format":"url","n":1,"prompt_optimizer":True})
        _download(_img_url(res), ref_path)
        print(f"    · 生成角色參考 _{story['id']}_ref.jpg")
        time.sleep(1.2)
    b = open(ref_path,"rb").read()
    return "data:image/jpeg;base64," + base64.b64encode(b).decode()

def gen_panel(key, key_name, subj, ref_datauri):
    payload = {"model":"image-01","prompt":SCENE.format(subj=subj),
        "aspect_ratio":"1:1","response_format":"url","n":1,"prompt_optimizer":True}
    if ref_datauri:
        payload["subject_reference"] = [{"type":"character","image_file":ref_datauri}]
    res = _post(key, payload)
    path = os.path.join(IMG_DIR, key_name + ".jpg")
    _download(_img_url(res), path)
    return path

def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    key = load_key()
    done=skip=fail=0
    for story in STORIES:
        need = [p for p in story["panels"] if not existing(p[0])]
        if not need:
            print(f"[{story['id']}] 全部已有，跳過"); skip += len(story["panels"]); continue
        print(f"[{story['id']}] 生成 {len(need)} 格" + ("（角色一致）" if story["char"] else "（自然）"))
        ref = get_ref_datauri(key, story) if story["char"] else None
        for k,subj,say in story["panels"]:
            if existing(k): print(f"    {k}  ⏭"); skip+=1; continue
            try:
                gen_panel(key, k, subj, ref); print(f"    {k}  ✓"); done+=1; time.sleep(1.3)
            except Exception as e:
                print(f"    {k}  ✗  {e}"); fail+=1
    print(f"\n完成：新生成 {done}、跳過 {skip}、失敗 {fail}。")

if __name__ == "__main__":
    main()
