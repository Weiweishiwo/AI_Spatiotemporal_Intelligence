# -*- coding: utf-8 -*-
"""构建脚本：把中国省界数据精简成 frontend/static/geo/china-provinces.js。

当前用的是第 2 种，源文件从这里下（阿里 DataV，含九段线，公开可直接 GET）：
  https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json
第 1 种（ECharts 的 china.json，要解码）已弃用：它不含南海诸岛，国内正式场合
用的中国地图按规范应包含。

支持两种输入：
  1. ECharts 的 china.json —— 坐标是 UTF8Encoding 压缩格式（hex 字符对 +
     delta + ZigZag + 量化 1/1024），需先解码；
  2. 普通 GeoJSON（如上面那份 DataV 的 100000_full.json）—— 直接用。
用 --keep-all 可对指定名字的要素跳过碎环过滤（九段线那种细长条不能被当碎岛丢掉）。

用法：
  python _build_china_geo.py <输入> <输出> [--keep-all 要素名,要素名]

产物是 `window.CHINA_GEO = {...};`，本脚本只跑一次，运行时不再依赖它。
"""
import json
import sys
from pathlib import Path

SCALE = 1024.0
MIN_RING_AREA = 0.02      # 小于这个面积（平方度）且在首环之外的环，当碎岛丢掉

# 当前采用的源（阿里 DataV，含九段线）。写进产物注释里，方便以后重新下载。
SOURCE_URL = "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json"


def decode_ring(s, ox, oy):
    """解压一圈坐标：hex 字符对 → ZigZag → delta 还原 → 反量化 → [lng, lat]"""
    pts = []
    px, py = ox, oy
    for i in range(0, len(s), 2):
        x = ord(s[i]) - 64
        y = ord(s[i + 1]) - 64
        x = (x >> 1) ^ (-(x & 1))
        y = (y >> 1) ^ (-(y & 1))
        px += x
        py += y
        pts.append([round(px / SCALE, 2), round(py / SCALE, 2)])
    return pts


def dedup(ring):
    """去掉相邻重复点（量化到 2 位小数后会大量出现）"""
    out = []
    for p in ring:
        if not out or out[-1] != p:
            out.append(p)
    return out


def ring_area(ring):
    """鞋带公式算近似面积，用来判断小块（碎岛）要不要丢"""
    a = 0.0
    for i in range(len(ring) - 1):
        a += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
    return abs(a) / 2


def geom_to_polys(geom, keep_all=False):
    """统一取到 [面][环][点]，兼容压缩格式与普通 GeoJSON。"""
    if geom["type"] == "Polygon":
        polys, offs = [geom["coordinates"]], [geom.get("encodeOffsets")]
    elif geom["type"] == "MultiPolygon":
        polys, offs = geom["coordinates"], geom.get("encodeOffsets")
    else:                                  # 别的类型（点/线）不参与板块
        return []

    out_polys, dropped = [], 0
    for pi, poly in enumerate(polys):
        poff = offs[pi] if offs else None
        new_rings = []
        for ri, ring in enumerate(poly):
            pts = (decode_ring(ring, poff[ri][0], poff[ri][1])
                   if isinstance(ring, str) else
                   [[round(p[0], 2), round(p[1], 2)] for p in ring])
            pts = dedup(pts)
            if len(pts) < 4:
                dropped += 1
                continue
            if not keep_all and new_rings and ring_area(pts) < MIN_RING_AREA:
                dropped += 1
                continue
            new_rings.append(pts)
        if new_rings:
            out_polys.append(new_rings)
    return out_polys, dropped


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    keep_all = set()
    if "--keep-all" in sys.argv:
        keep_all = set(sys.argv[sys.argv.index("--keep-all") + 1].split(","))

    raw = json.loads(src.read_text(encoding="utf-8"))
    features, kept, dropped = [], 0, 0
    label = {"type": "FeatureCollection", "features": []}

    for feat in raw["features"]:
        props = feat.get("properties") or {}
        name = props.get("name") or ""
        adcode = props.get("adcode") or ""
        # DataV 的九段线要素没有名字，只有 adcode，给它个能显示的称呼
        if not name and adcode == "100000_JD":
            name = "南海诸岛"
        polys, d = geom_to_polys(feat["geometry"],
                                 keep_all=(name in keep_all or adcode in keep_all))
        kept += sum(len(p) for p in polys)
        dropped += d
        if not polys:
            continue
        features.append({
            "type": "Feature",
            "properties": {"name": name},
            # 一律输出 MultiPolygon（coordinates[面][环][点]），层级统一，Leaflet 两种都认
            "geometry": {"type": "MultiPolygon", "coordinates": polys},
        })

    gj = {"type": "FeatureCollection", "features": features}
    payload = json.dumps(gj, ensure_ascii=False, separators=(",", ":"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "/* 中国省界轮廓（普通 GeoJSON，由 pure_html_map/_build_china_geo.py 精简生成）\n"
        "   源：%s\n"
        "       （本文件是精简产物，别手改；要更新就重下源文件、重跑脚本）\n"
        "   重建：python _build_china_geo.py <源文件> static/geo/china-provinces.js --keep-all 100000_JD\n"
        "        （--keep-all 是为了保住九段线：那几段又细又长，会被碎环过滤误删）\n"
        "   用途：/map 页「全国」视图的底图板块。加载后为 window.CHINA_GEO。 */\n"
        "window.CHINA_GEO = %s;\n" % (SOURCE_URL, payload),
        encoding="utf-8",
    )

    pts = [p for f in features for poly in f["geometry"]["coordinates"]
           for ring in poly for p in ring]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    print("features:", len(features), "| rings kept/dropped:", kept, "/", dropped)
    print("lng %.2f..%.2f  lat %.2f..%.2f" % (min(xs), max(xs), min(ys), max(ys)))
    print("output KB:", round(out.stat().st_size / 1024, 1))


main()
