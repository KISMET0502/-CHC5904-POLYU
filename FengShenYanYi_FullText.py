# -*- coding: utf-8 -*-
"""
CText《封神演义》抓取器 v1.3 (全文章节版)
- 断点续传：每回写入 CSV，manifest.json 记录已完成回目
- 限流检测：遇到 ERR_REQUEST_LIMIT 优雅落盘退出
- readlink 返回 dict/str 兼容，失败时 API 兜底
- gettextasobject 失败回退到 gettextasparagraphlist
- 【修改】：本版本只输出 fengshen_fulltext.csv，每行一章
用法示例：
  pip install ctext pandas tqdm requests
  python scrape_fengshen_ctext_fulltext.py --chapters 1-100 --outdir ./out --remap gb --delay 1.0
"""
import argparse, os, time, re, sys, json
from typing import List, Dict, Any

import requests
import pandas as pd
from tqdm import tqdm

# ---- ctext 库 ----
try:
    from ctext import (
        setlanguage, setremap, readlink,
        gettextasobject, gettextasparagraphlist
    )
except Exception as e:
    print("请先安装依赖：pip install ctext pandas tqdm requests", file=sys.stderr)
    raise

# 【修改点 1】: 将 URL 目标从 xiyouji 切换到 fengshen-yanyi
# 注意：使用 /1/zh, /2/zh... 这种数字索引路径，以匹配脚本的数字迭代逻辑
CH_URL = "https://ctext.org/fengshen-yanyi/{n}/zh"


# 【修改】：不再需要句子拆分
# SPLIT_PAT = re.compile(r"(?<=[。！？!?；;])")

def parse_range(spec: str) -> List[int]:
    if not spec:
        return list(range(1, 101))
    nums: List[int] = []
    for part in [p.strip() for p in spec.split(",") if p.strip]:
        if "-" in part:
            a, b = part.split("-", 1)
            a, b = int(a), int(b)
            step = 1 if a <= b else -1
            nums.extend(range(a, b + step, step))
        else:
            nums.append(int(part))
    return sorted(set(nums))


def resolve_urn(url: str, delay: float) -> str:
    """URL -> URN；兼容 readlink 返回 dict/str，失败则 API 兜底。"""
    last_err = None
    try:
        res = readlink(url)
        if isinstance(res, dict):
            urn = res.get("urn") or res.get("textRef") or res.get("link")
            if not isinstance(urn, str):
                urn = next((v for v in res.values() if isinstance(v, str) and v.startswith("ctp:")), None)
            if not urn:
                raise ValueError(f"readlink 返回无 URN: {res}")
        else:
            urn = str(res)
        return urn
    except Exception as e:
        last_err = e
    # 兜底：API
    try:
        r = requests.get("https://api.ctext.org/readlink", params={"url": url}, timeout=15)
        r.raise_for_status()
        j = r.json() if "application/json" in r.headers.get("content-type", "") else json.loads(r.text)
        urn = j.get("urn") or j.get("textRef") or j.get("link")
        if not isinstance(urn, str):
            urn = next((v for v in j.values() if isinstance(v, str) and v.startswith("ctp:")), None)
        if not urn:
            raise ValueError(f"API readlink 无 URN: {j}")
        time.sleep(delay)
        return urn
    except Exception as e2:
        raise RuntimeError(f"resolve_urn 失败：readlink_err={last_err} ; api_err={e2}")


def fetch_chapter(n: int, delay: float = 0.8, retries: int = 1) -> Dict[str, Any]:
    """返回 {'chapter_no','chapter_title','urn','paragraphs','source_url'}"""
    url = CH_URL.format(n=n)
    last_err = None
    for attempt in range(retries + 1):
        try:
            urn = resolve_urn(url, delay)
            # 先拿结构化（可取标题），失败就直接取段落
            try:
                data = gettextasobject(urn)
                title = data.get("title") or f"第{n}回"
                paragraphs = data.get("fulltext") or []
                if not paragraphs:
                    paragraphs = gettextasparagraphlist(urn) or []
            except Exception:
                title = f"第{n}回"
                paragraphs = gettextasparagraphlist(urn) or []
            paragraphs = [p.strip() for p in paragraphs if p and str(p).strip()]
            if not paragraphs:
                raise ValueError("空章节或未取到段落")
            time.sleep(delay)
            return {
                "chapter_no": n,
                "chapter_title": title,
                "urn": urn,
                "paragraphs": paragraphs,
                "source_url": url,
            }
        except Exception as e:
            last_err = e
            msg = str(e)
            # 硬性限流就不再重试，交给上层处理
            if "ERR_REQUEST_LIMIT" in msg or "达到请求限制" in msg:
                raise
            time.sleep(delay * (attempt + 1))
    raise RuntimeError(f"抓取第 {n} 回失败：{last_err}")


# 【修改】：移除 split_sentences, to_paragraph_rows, to_sentence_rows 函数

def append_csv(path: str, rows: List[Dict[str, Any]]):
    df = pd.DataFrame(rows)
    file_exists = os.path.exists(path)
    df.to_csv(path, mode="a" if file_exists else "w", index=False, encoding="utf-8-sig", header=not file_exists)


def load_manifest(mpath: str) -> Dict[str, Any]:
    if os.path.exists(mpath):
        with open(mpath, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                pass
    # 【修改】：更新 manifest 计数器名称
    return {"fetched": [], "chapter_rows": 0}


def save_manifest(mpath: str, man: Dict[str, Any]):
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2)


def main():
    # 【修改点 4】: 更新脚本描述
    ap = argparse.ArgumentParser(description="CText《封神演义》抓取（断点续传 v1.3 - 全文版）")
    ap.add_argument("--chapters", type=str, default="", help="回目选择，如 '1-20,59,72-74'；默认 1-100")
    ap.add_argument("--outdir", type=str, default="./out", help="输出目录")
    ap.add_argument("--delay", type=float, default=0.8, help="API 调用间隔秒")
    ap.add_argument("--remap", type=str, default="", help="字符映射：留空=繁体，'gb'=简体")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # 【修改】：更新输出文件名，只保留一个 CSV
    fulltext_path = os.path.join(args.outdir, "fengshen_fulltext.csv")
    man_path = os.path.join(args.outdir, "manifest.json")

    setlanguage("zh")
    if args.remap:
        setremap(args.remap)  # 'gb' -> 简体

    requested = parse_range(args.chapters)
    man = load_manifest(man_path)
    fetched_set = set(man.get("fetched", []))
    to_fetch = [n for n in requested if n not in fetched_set]

    if len(requested) > 10:
        print(f"将抓取回目：{requested[:10]} ... {requested[-10:]}")
    else:
        print(f"将抓取回目：{requested}")
    done_preview = sorted(fetched_set)[:10]
    print(f"已完成回目（跳过）：{done_preview if done_preview else []}")

    try:
        for n in tqdm(to_fetch, desc="Fetching chapters"):
            try:
                item = fetch_chapter(n, delay=args.delay)

                # 【修改】：合并所有段落为一个字符串，用换行符分隔
                full_text = "\n".join(item["paragraphs"])

                # 【修改】：构建单行数据
                row_data = {
                    "book": "封神演義",
                    "chapter_no": item["chapter_no"],
                    "chapter_title": item["chapter_title"],
                    "full_text": full_text,
                    "source_url": item["source_url"],
                    "urn": item["urn"],
                }

                # 【修改】：将这一行数据（包装在列表中）追加到 CSV
                # append_csv 期望一个 List[Dict]，所以我们传入 [row_data]
                append_csv(fulltext_path, [row_data])

                # --- 更新 manifest ---
                fetched_set.add(n)
                man["fetched"] = sorted(fetched_set)
                # 【修改】：更新新的计数器
                man["chapter_rows"] = int(man.get("chapter_rows", 0)) + 1
                save_manifest(man_path, man)

            except Exception as e:
                msg = str(e)
                save_manifest(man_path, man)
                if "ERR_REQUEST_LIMIT" in msg or "达到请求限制" in msg:
                    print("\n[额度限制] 达到请求上限，已保存进度（manifest.json / CSV）。下次重跑会自动续传剩余回目。")
                    return
                else:
                    print(f"\n[警告] 第 {n} 回失败：{msg}（已保存进度，继续下一回）")
                    # 继续尝试后续回目；如需严格终止，可改为 raise
                    continue

        # 【修改】：更新完成后的提示信息
        print(f"\n[完成] 已抓取：{len(fetched_set)} 回；累计 {man.get('chapter_rows', 0)} 行（章）。")
        print(f"全文CSV：{fulltext_path}\n清单：{man_path}")

    except KeyboardInterrupt:
        save_manifest(man_path, man)
        print("\n[中断] 手动终止。已保存进度。")


if __name__ == "__main__":
    main()