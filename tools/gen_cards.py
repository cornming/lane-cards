"""用 Gemini 產生三路卡陣的卡牌插圖。

需求：
  pip install google-genai pillow
  設定環境變數 GEMINI_API_KEY（到 Google AI Studio 申請）

用法：
  python tools/gen_cards.py                 # 產生 cards/ 裡還沒有的圖
  python tools/gen_cards.py --only wolf,archer --force
  python tools/gen_cards.py --model gemini-2.5-flash-image

產出：cards/<卡牌id>.webp（384×384）。產完後 commit 並 push，遊戲會自動改用插圖。
"""
import argparse, json, pathlib, sys, time
from io import BytesIO

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "cards"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemini-2.5-flash-image")
    ap.add_argument("--only", default="", help="只產生這些 id，逗號分隔")
    ap.add_argument("--force", action="store_true", help="已存在也重新產生")
    ap.add_argument("--size", type=int, default=384)
    args = ap.parse_args()

    try:
        from google import genai
        from PIL import Image
    except ImportError:
        sys.exit("請先執行：pip install google-genai pillow")

    data = json.loads((ROOT / "tools" / "card-prompts.json").read_text(encoding="utf-8"))
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    OUT.mkdir(exist_ok=True)
    client = genai.Client()  # 讀取 GEMINI_API_KEY

    for card in data["cards"]:
        cid, prompt = card["id"], card["prompt"]
        if only and cid not in only:
            continue
        dst = OUT / f"{cid}.webp"
        if dst.exists() and not args.force:
            print(f"略過 {cid}（已存在）")
            continue
        for attempt in range(3):
            try:
                resp = client.models.generate_content(model=args.model, contents=[prompt])
                img = None
                for part in resp.candidates[0].content.parts:
                    if getattr(part, "inline_data", None) and part.inline_data.data:
                        img = Image.open(BytesIO(part.inline_data.data)).convert("RGB")
                        break
                if img is None:
                    raise RuntimeError("回應裡沒有圖片")
                w, h = img.size
                s = min(w, h)
                img = img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((args.size, args.size))
                img.save(dst, "WEBP", quality=82)
                print(f"完成 {cid} → {dst.relative_to(ROOT)}")
                break
            except Exception as e:  # 網路或配額問題就稍等重試
                print(f"{cid} 第 {attempt + 1} 次失敗：{e}")
                time.sleep(5 * (attempt + 1))
        time.sleep(1)

if __name__ == "__main__":
    main()
