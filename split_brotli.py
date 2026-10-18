#!/usr/bin/env python3
"""下载 2000-2010 共 11 年解读数据，按日期分片并 brotli 压缩。

在 GitHub Actions 云端运行，本地不跑（避免手机发热）。
产物：data/YYYY-MM-DD.br（每天 24 条：12 时辰 × 男女）
"""
import json, os, subprocess, sys
import brotli

YEARS = range(2000, 2011)
os.makedirs('data', exist_ok=True)

all_days = []

for year in YEARS:
    src = f'raw/year-{year}.jsonl.zst'
    if not os.path.exists(src):
        print(f'缺文件 {src}，跳过', flush=True)
        continue

    p = subprocess.Popen(['zstd', '-dc', '--long=27', src],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    buckets = {}
    for raw in p.stdout:
        raw = raw.strip()
        if not raw:
            continue
        r = json.loads(raw)
        day = f"{r['y']}-{r['m']:02d}-{r['d']:02d}"
        rec = {'h': r['h'], 'g': r['g'], 'ms': r['ms'], 'c': r['c']}
        buckets.setdefault(day, []).append(rec)
    p.wait()

    for day, recs in buckets.items():
        raw = json.dumps(recs, ensure_ascii=False, separators=(',', ':')).encode()
        br = brotli.compress(raw, quality=10)
        with open(f'data/{day}.br', 'wb') as f:
            f.write(br)
        all_days.append(day)

    print(f'{year} 完成：{len(buckets)} 天', flush=True)

all_days = sorted(set(all_days))
with open('data/index.json', 'w') as f:
    json.dump({'years': list(YEARS), 'days': all_days}, f)
print(f'总计 {len(all_days)} 天', flush=True)
