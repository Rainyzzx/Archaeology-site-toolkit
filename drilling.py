import arcpy
import matplotlib.pyplot as plt
from collections import Counter
import random
import matplotlib.font_manager as fm

# 输入参数
input_layer = arcpy.GetParameter(0)
field_name = "drilling_r"

# --- 字段值统计 ---
values = [row[0] for row in arcpy.da.SearchCursor(input_layer, [field_name]) if row[0]]
counter = Counter(values)

# --- 获取地图图层对象 ---
aprx = arcpy.mp.ArcGISProject("CURRENT")
map_obj = aprx.activeMap
layer_obj = [lyr for lyr in map_obj.listLayers() if lyr.name == input_layer.name][0]

# --- 设置符号化 ---
sym = layer_obj.symbology
if hasattr(sym, 'renderer') and sym.renderer.type == 'UniqueValueRenderer':
    sym.renderer.fields = [field_name]
    sym.renderer.field1 = field_name
    sym.renderer.removeAllValues()

    # 添加类别及颜色
    for val in counter.keys():
        sym.renderer.addValue(val)
        symbol = sym.renderer.getSymbol(val)
        symbol.color = [random.randint(0, 255) for _ in range(3)] + [100]
        sym.renderer.updateSymbol(val, symbol)

    # 应用渲染
    layer_obj.symbology = sym
else:
    arcpy.AddWarning("图层不支持唯一值渲染")

# --- 中文字体支持 ---
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# --- 饼图数据准备 ---
labels = list(counter.keys())
sizes = list(counter.values())

# --- 绘制饼图 ---
plt.figure(figsize=(8, 8))
wedges, texts, autotexts = plt.pie(
    sizes,
    autopct='%1.1f%%',
    startangle=90,
    pctdistance=0.8,
    wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
)

# --- 添加图例显示中文标签 ---
plt.legend(
    wedges,
    labels,
    title="钻探情况类别",
    loc="center left",
    bbox_to_anchor=(1, 0, 0.5, 1),  # 图例放在图外右侧
    fontsize=11
)

# 设置标题与美化
for autotext in autotexts:
    autotext.set_fontsize(12)

plt.title("探孔钻探情况统计饼图", fontsize=14)
plt.axis("equal")
plt.tight_layout()
plt.show()