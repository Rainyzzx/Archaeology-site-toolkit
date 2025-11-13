# -*- coding: utf-8 -*-
import arcpy
from arcpy.sa import *

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

# ====== 输入参数 ======
input_sites = arcpy.GetParameterAsText(0)          # 遗址点
input_slope_cost = arcpy.GetParameterAsText(1)     # 成本图层（已生成的坡度图）
output_path = "memory/传播路径"                     # 输出路径图层

# ====== 获取点列表 ======
arcpy.AddMessage("📌 正在读取遗址点...")
points = []
with arcpy.da.SearchCursor(input_sites, ["OID@", "SHAPE@"]) as cursor:
    for row in cursor:
        points.append((row[0], row[1]))

arcpy.AddMessage(f"✔️ 遗址点共计：{len(points)} 个，将生成 {len(points)*(len(points)-1)//2} 条路径（理论值）")

# ====== 遍历组合生成路径 ======
path_list = []

for i in range(len(points)):
    for j in range(i + 1, len(points)):
        oid1, _ = points[i]
        oid2, _ = points[j]
        arcpy.AddMessage(f"→ 正在处理路径：{oid1} → {oid2}")

        try:
            # ====== 创建起点与终点图层 ======
            start_fc = arcpy.env.scratchGDB + "/start"
            end_fc = arcpy.env.scratchGDB + "/end"

            arcpy.MakeFeatureLayer_management(input_sites, "start_lyr")
            arcpy.SelectLayerByAttribute_management("start_lyr", "NEW_SELECTION", f"OBJECTID = {oid1}")
            arcpy.CopyFeatures_management("start_lyr", start_fc)

            arcpy.MakeFeatureLayer_management(input_sites, "end_lyr")
            arcpy.SelectLayerByAttribute_management("end_lyr", "NEW_SELECTION", f"OBJECTID = {oid2}")
            arcpy.CopyFeatures_management("end_lyr", end_fc)

            # ====== 空图层检查 ======
            if int(arcpy.GetCount_management(start_fc)[0]) == 0 or int(arcpy.GetCount_management(end_fc)[0]) == 0:
                arcpy.AddWarning(f"⛔ OBJECTID {oid1} 或 {oid2} 无效，跳过")
                continue

            # ====== 成本路径分析 ======
            cost_dist = CostDistance(start_fc, input_slope_cost)
            backlink = CostBackLink(start_fc, input_slope_cost)
            path_raster = CostPath(end_fc, cost_dist, backlink, "EACH_CELL")

            # ====== 栅格转线 ======
            path_line = f"in_memory/path_{oid1}_{oid2}"
            polyline = arcpy.RasterToPolyline_conversion(path_raster, path_line, "ZERO", 0, "NO_SIMPLIFY")
            path_list.append(polyline)

        except Exception as e:
            arcpy.AddWarning(f"❌ 路径 {oid1} → {oid2} 失败，原因：{e}")
            continue

# ====== 合并输出 ======
if path_list:
    arcpy.AddMessage("🧩 正在合并所有路径图层...")
    arcpy.Merge_management(path_list, output_path)
    arcpy.SetParameter(2, output_path)
    arcpy.AddMessage("✅ 成功生成传播路径图层：memory/传播路径")
else:
    arcpy.AddWarning("⚠️ 所有路径均失败，未生成任何图层。")
