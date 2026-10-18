#!/usr/bin/env python3
"""下载 2000-2010 解读数据，按日期分片并 zstd 压缩。

用 zstd 而非 brotli：浏览器的 DecompressionStream 不支持 brotli
（只有 Safari 认），安卓 Chrome 会报 Unsupported compression format。
zstd 用纯 JS 的 fzstd 解码（8KB），全平台可用。
"""
import json, os, subprocess

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
        buckets.setdefault(day, []).append(
            {'h': r['h'], 'g': r['g'], 'ms': r['ms'], 'c': r['c']})
    p.wait()

    for day, recs in buckets.items():
        raw = json.dumps(recs, ensure_ascii=False, separators=(',', ':')).encode()
        # 写临时文件再调 zstd，避免 Python 绑定的依赖
        tmp = f'/tmp/_{day}.json'
        with open(tmp, 'wb') as f:
            f.write(raw)
        subprocess.run(['zstd', '-19', '-q', '-f', tmp, '-o', f'data/{day}.json.zst'],
                       check=True)
        os.remove(tmp)
        all_days.append(day)

    print(f'{year} 完成：{len(buckets)} 天', flush=True)

all_days = sorted(set(all_days))
with open('data/index.json', 'w') as f:
    json.dump({'years': list(YEARS), 'days': all_days}, f)
print(f'总计 {len(all_days)} 天', flush=True)
