import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ===== 数据（Overall） =====
rows = [
    # Instruct Model Based
    {"method":"GPT-5",            "model":"GPT-5",             "group":"base",     "EX":55.74, "ROSE":88.93},
    {"method":"Alpha-SQL-32B",    "model":"Qwen2.5 Coder",     "group":"instruct", "EX":69.35, "ROSE":81.09},
    {"method":"OpenSearch-SQL",       "model":"DeepSeek-Chat",       "group":"instruct", "EX":69.37, "ROSE":80.96},
    {"method":"RSL-SQL (DS)",   "model":"DeepSeek-Chat",       "group":"instruct", "EX":62.50, "ROSE":74.15},
    {"method":"DeepSeek-Chat",      "model":"DeepSeek-Chat",       "group":"base",     "EX":52.13, "ROSE":72.21},
    {"method":"RSL-SQL (GPT)",     "model":"GPT-4o",            "group":"instruct", "EX":66.88, "ROSE":81.92},
    {"method":"GPT-4o",           "model":"GPT-4o",            "group":"base",     "EX":52.20, "ROSE":71.37},
    {"method":"SuperSQL",         "model":"GPT-4",             "group":"instruct", "EX":53.73, "ROSE":61.18},
    {"method":"TA-SQL",           "model":"GPT-4",             "group":"instruct", "EX":51.06, "ROSE":57.63},
    {"method":"DAIL-SQL",         "model":"GPT-4",             "group":"instruct", "EX":48.79, "ROSE":55.60},
    {"method":"GPT-4",            "model":"GPT-4",             "group":"base",     "EX":48.98, "ROSE":66.53},
    {"method":"CoT",              "model":"GPT-3.5",           "group":"instruct", "EX":25.87, "ROSE":32.83},
    {"method":"C3-SQL",           "model":"GPT-3.5",           "group":"instruct", "EX":42.36, "ROSE":46.29},
    {"method":"GPT-3.5",          "model":"GPT-3.5",           "group":"base",     "EX":41.22, "ROSE":50.61},
    # Fine-tuned Model Based
    {"method":"CSC-SQL-32B",      "model":"FT (XiYan-Qwen2.5)","group":"finetune", "EX":71.52, "ROSE":78.27},
    {"method":"OmniSQL-32B",      "model":"FT (Qwen2.5 Coder)","group":"finetune", "EX":68.92, "ROSE":79.49},
    {"method":"CodeS-15B",        "model":"FT (StarCoder)",    "group":"finetune", "EX":50.77, "ROSE":49.01},
    {"method":"CHESS-V1",         "model":"FT (Mixed)",        "group":"finetune", "EX":59.28, "ROSE":62.24},
    {"method":"RESDSQL-3B",       "model":"FT (T5)",           "group":"finetune", "EX":35.87, "ROSE":34.57},
]

# ===== 样式 =====
model_colors = {
    "GPT-3.5":         "#1f77b4",
    "GPT-4":           "#ff7f0e",
    "GPT-4o":          "#d62728",
    "GPT-5":           "#2ca02c",
    "DeepSeek-Chat":   "#9467bd",
}
ft_color = "#7f7f7f"  # fine-tuned 统一灰

def marker_of(group):
    if group == "base":     return "*"
    if group == "instruct": return "o"
    return "^"  # finetune

def color_of(model, group):
    if group == "finetune":
        return ft_color
    if model == "Qwen2.5 Coder":
        return ft_color
    return model_colors.get(model, "#333333")

# ===== 绘图参数 =====
origin = 25
xmin, xmax = origin, 78
ymin, ymax = 30, 90
# 计算合适的figsize，使纵轴稍微压缩
x_range = xmax - xmin  # 78 - 25 = 53
y_range = ymax - ymin  # 90 - 30 = 60
aspect_ratio = y_range / x_range * 0.9  # 60/53 * 0.9 ≈ 1.02
fig, ax = plt.subplots(figsize=(19, 20 * aspect_ratio))

# 先画点
points = []  # (name, x, y)
for r in rows:
    mkr   = marker_of(r["group"])
    color = color_of(r["model"], r["group"])
    # 继续小幅缩小点面积（s 为面积，非半径）
    size  = 1200 if mkr == "*" else 950
    # 若低于下限则钳位在边界上（同时仍可读）
    x, y = r["EX"], r["ROSE"]
    cx, cy = (max(x, xmin), max(y, ymin))
    ax.scatter(cx, cy, s=size, marker=mkr,
               facecolors=color, edgecolors="black", linewidths=0.5, zorder=3)
    points.append((r["method"], cx, cy))

# 初始化文本对象（大部分在下方，特定标签在指定位置）
texts = []
for name, x, y in points:
    if name == "DeepSeek-Chat":
        # 上方标签（上移）
        texts.append(ax.text(x, y+0.9, name, fontsize=24, ha='center', va='bottom', zorder=4))
    elif name == "OpenSearch-SQL":
        # 右下角标签
        texts.append(ax.text(x+0.2, y-0.7, name, fontsize=24, ha='left', va='top', zorder=4))
    elif name in ["RSL-SQL (GPT)", "OmniSQL-32B"]:
        # 左下角标签（向左调整）
        texts.append(ax.text(x-0.3, y-0.7, name, fontsize=24, ha='right', va='top', zorder=4))
    elif name == "Alpha-SQL-32B":
        # 右上角标签（上移）
        texts.append(ax.text(x-0.2, y+1.0, name, fontsize=24, ha='left', va='bottom', zorder=4))
    elif name == "CoT":
        # 右下角标签
        texts.append(ax.text(x+0.2, y-0.7, name, fontsize=24, ha='left', va='top', zorder=4))
    elif name == "TA-SQL":
        # 右下角标签（右移并下移，左对齐、顶部对齐）
        texts.append(ax.text(x+0.4, y-0.8, name, fontsize=24, ha='left', va='top', zorder=4))
    else:
        # 默认下方标签
        texts.append(ax.text(x, y-1, name, fontsize=24, ha='center', va='top', zorder=4))

# 45° 参考线（ROSE=EX），从 (30,30) 到右上角
ax.plot([origin, xmax], [origin, xmax],
        linestyle="--", color="#888888", linewidth=1.2, zorder=1)
# 在虚线上添加标签
ax.text(65, 66, "ROSE=EX", fontsize=24, color="black", weight='bold', ha='left', va='bottom', 
        rotation=45)

# 轴、网格、标题
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)
ax.set_xlabel("EX", fontsize=28)
ax.set_ylabel("ROSE", fontsize=28)
ax.tick_params(axis='both', which='major', labelsize=20)
ax.grid(True, linestyle="--", alpha=0.35, zorder=0)

# 颜色图例（左上）
color_handles = [Line2D([0],[0], marker="o", color="w", markeredgecolor="black",
                        markerfacecolor=c, markersize=20, label=lbl)
                 for lbl, c in model_colors.items()]
leg_colors = ax.legend(handles=color_handles,
                       loc="upper left", frameon=True, fontsize=23)
ax.add_artist(leg_colors)

# 形状图例（右下）
shape_handles = [
    Line2D([0],[0], marker="*", color="w", markeredgecolor="black",
           markerfacecolor="#bbbbbb", markersize=20, label="Base Model"),
    Line2D([0],[0], marker="o", color="w", markeredgecolor="black",
           markerfacecolor="#bbbbbb", markersize=20, label="Engineered System"),
    Line2D([0],[0], marker="^", color="w", markeredgecolor="black",
           markerfacecolor=ft_color,   markersize=20, label="Fine-tuned Method"),
]
ax.legend(handles=shape_handles,
          loc="lower right", frameon=True, fontsize=23)

# 标签已经直接放在点的下方，无需额外处理

plt.tight_layout()
plt.savefig("figure/scatter.png", dpi=200)
print("Saved figure to figure/scatter.png")

# Convert PNG to PDF using Pillow
from PIL import Image
img = Image.open("figure/scatter.png")
# Convert RGBA to RGB if necessary
if img.mode == 'RGBA':
    img = img.convert('RGB')
img.save("figure/scatter.pdf", "PDF")
print("Saved figure to figure/scatter.pdf")
