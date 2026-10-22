# -*- coding: utf-8 -*-
"""Check a draft against the 兽楼处体 quantitative targets.

Usage:
    python check_draft.py <draft.md> [--json]

Exit code 0 = all hard targets met; 1 = at least one hard target missed.
"""
import re
import sys
import json

CN = re.compile(r'[\u4e00-\u9fa5]')
SENT_SPLIT = re.compile(r'[。！？!?…]+["”’）)]*')
NUM_UNIT = re.compile(r'\d+(?:\.\d+)?\s*(?:亿|万|万亿|%|％|年|月|日|块|元|美元|平方米|平方公里|公里|里|人|家|条|艘|岁|层|度)')

TARGETS = {
    'chars':      (3000, 4500, '全文汉字数'),
    'paragraphs': (90, 110, '段落数'),
    'para_median': (26, 38, '段落长度中位数'),
    'short_ratio': (20.0, 30.0, '短段落(<=15字)占比%'),
    'sent_median': (18, 30, '句长中位数'),
    'num_density': (8.0, 12.0, '数字密度(处/千字)'),
    'colon_drop':  (12, 18, '冒号甩段次数'),
    'sections':    (3, 6, '章节数(裸数字分隔)'),
    'last_line':   (4, 30, '末行字数'),
}


def median(xs):
    xs = sorted(xs)
    if not xs:
        return 0
    return xs[len(xs) // 2]


def check(path: str) -> dict:
    text = open(path, encoding='utf-8').read()
    lines = text.split('\n')
    # measure body prose only: skip headings, block-quotes and horizontal rules
    paras = [
        p.strip() for p in lines
        if p.strip()
        and not p.strip().startswith('#')
        and not p.strip().startswith('>')
        and not set(p.strip()) <= {'-', '*', '_'}
    ]

    n_chars = len(CN.findall('\n'.join(paras)))
    # bare-number lines are section dividers, not prose paragraphs
    body_paras = [p for p in paras if not re.fullmatch(r'\d{1,2}', p)]
    para_lens = [len(CN.findall(p)) for p in body_paras]
    sents = [len(CN.findall(s)) for s in SENT_SPLIT.split('\n'.join(paras))]
    sents = [s for s in sents if s > 0]
    n_num = len(NUM_UNIT.findall('\n'.join(paras)))
    colon = sum(1 for p in paras if p.endswith(('：', ':')))
    sections = max([int(p) for p in paras if re.fullmatch(r'\d{1,2}', p)] or [0])
    last = len(CN.findall(paras[-1])) if paras else 0

    return {
        'chars': n_chars,
        'paragraphs': len(body_paras),
        'para_median': median(para_lens),
        'short_ratio': round(100.0 * sum(1 for x in para_lens if x <= 15) / max(len(para_lens), 1), 1),
        'sent_median': median(sents),
        'num_density': round(1000.0 * n_num / max(n_chars, 1), 2),
        'colon_drop': colon,
        'sections': sections,
        'last_line': last,
        'exclamations': text.count('！') + text.count('!'),
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    path = sys.argv[1]
    m = check(path)
    if '--json' in sys.argv:
        print(json.dumps(m, ensure_ascii=False, indent=2))
        sys.exit(0)

    print('指标检查：%s\n' % path)
    print('%-22s %10s %16s  %s' % ('指标', '实测', '目标区间', '判定'))
    print('-' * 66)
    failed = 0
    for key, (lo, hi, label) in TARGETS.items():
        v = m[key]
        ok = lo <= v <= hi
        if not ok:
            failed += 1
        print('%-22s %10s %16s  %s' % (
            label, v, '%d ~ %d' % (lo, hi) if isinstance(lo, int) else '%.1f ~ %.1f' % (lo, hi),
            'OK' if ok else 'MISS'))
    print('-' * 66)
    print('感叹号数量：%d（目标 <= 3）  %s' % (
        m['exclamations'], 'OK' if m['exclamations'] <= 3 else 'MISS'))
    if m['exclamations'] > 3:
        failed += 1

    if failed:
        print('\n%d 项未达标，请按 style-code.md 调整后再交付。' % failed)
        sys.exit(1)
    print('\n全部量化指标达标。继续跑 self-check.md 的技法与红线清单。')
    sys.exit(0)


if __name__ == '__main__':
    main()
