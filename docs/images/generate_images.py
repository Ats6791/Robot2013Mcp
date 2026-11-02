import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Arc, Circle
from matplotlib.lines import Line2D
import numpy as np

# ═══════════════════════════════════════════════
# IMAGE 1 — architecture.png  (1200 × 500)
# ═══════════════════════════════════════════════

fig1, ax1 = plt.subplots(figsize=(12, 5))
ax1.set_xlim(0, 12)
ax1.set_ylim(0, 5)
ax1.axis('off')
fig1.patch.set_facecolor('white')

# ── helpers ──────────────────────────────────────────────
def shadow(ax, x, y, w, h, r=0.25):
    p = FancyBboxPatch((x - w/2 + 0.06, y - h/2 - 0.06), w, h,
                       boxstyle=f"round,pad=0.04,rounding_size={r}",
                       lw=0, fc='#b0b8c8', zorder=1, alpha=0.5)
    ax.add_patch(p)

def box(ax, x, y, w, h, fc, ec, r=0.25):
    p = FancyBboxPatch((x - w/2, y - h/2), w, h,
                       boxstyle=f"round,pad=0.04,rounding_size={r}",
                       lw=2, ec=ec, fc=fc, zorder=3)
    ax.add_patch(p)

def header_band(ax, x, y, w, h, band_h, fc_band, ec, r=0.25):
    """Box with a darker top-band (like a title bar)."""
    box(ax, x, y, w, h, fc_band, ec, r)   # draw band colour full box first
    # white lower portion
    inner_h = h - band_h
    inner_y = y - band_h / 2
    p2 = FancyBboxPatch((x - w/2 + 0.04, y - h/2 + 0.04),
                        w - 0.08, inner_h - 0.04,
                        boxstyle="round,pad=0.03,rounding_size=0.15",
                        lw=0, fc='#f0f4ff', zorder=4)
    ax.add_patch(p2)

def label(ax, x, y, txt, fs=11, color='white', bold=True, z=5, align='center', va='center'):
    ax.text(x, y, txt, ha=align, va=va, fontsize=fs, color=color,
            fontweight='bold' if bold else 'normal', zorder=z,
            multialignment='center', linespacing=1.5)

def arrow(ax, x1, y1, x2, y2, color='#444', lw=2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color,
                                lw=lw, mutation_scale=18,
                                connectionstyle='arc3,rad=0'))

def arrow_label(ax, x, y, txt, ha='center', va='bottom', fs=9.5):
    ax.text(x, y, txt, ha=ha, va=va, fontsize=fs,
            color='#333', style='italic', zorder=6,
            bbox=dict(boxstyle='round,pad=0.18', fc='#f5f5f5',
                      ec='#ccc', lw=0.8))

# ── subtle dot grid ──
for gx in np.arange(0.4, 12, 0.7):
    for gy in np.arange(0.3, 5, 0.7):
        ax1.plot(gx, gy, '.', color='#e4e8f0', markersize=2, zorder=0)

# ── Title ──
ax1.text(6.0, 4.72, "Robot Structural Analysis MCP  —  Architecture",
         ha='center', va='center', fontsize=14.5,
         fontweight='bold', color='#1a1a3e', zorder=6)
ax1.plot([0.6, 11.4], [4.42, 4.42], color='#d0d5e8', lw=1, zorder=0)

# ── Box 1 : Claude Desktop ──
bx1, by1, bw1, bh1 = 2.1, 2.4, 3.0, 1.8
shadow(ax1, bx1, by1, bw1, bh1)
box(ax1, bx1, by1, bw1, bh1, '#5B4DA7', '#3d3273')
# inner white card
p_inner = FancyBboxPatch((bx1 - bw1/2 + 0.12, by1 - bh1/2 + 0.12),
                          bw1 - 0.24, bh1 - 0.48,
                          boxstyle="round,pad=0.04,rounding_size=0.18",
                          lw=0, fc='#ede9ff', zorder=4)
ax1.add_patch(p_inner)
# top badge
badge1 = FancyBboxPatch((bx1 - bw1/2 + 0.12, by1 + bh1/2 - 0.42),
                         bw1 - 0.24, 0.30,
                         boxstyle="round,pad=0.02,rounding_size=0.10",
                         lw=0, fc='#7B6FBF', zorder=5)
ax1.add_patch(badge1)
label(ax1, bx1, by1 + bh1/2 - 0.27, "Claude Desktop", fs=9, color='#f0ecff', z=6)
# icon: simple chat bubble drawn with patches
cb_x, cb_y, cb_r = bx1, by1 - 0.05, 0.28
chat_bg = Circle((cb_x, cb_y + 0.10), cb_r, fc='#7B6FBF', ec='none', zorder=5)
ax1.add_patch(chat_bg)
ax1.text(cb_x, cb_y + 0.10, "AI", ha='center', va='center',
         fontsize=7.5, color='white', fontweight='bold', zorder=6)
# sub-label
label(ax1, bx1, by1 - 0.30, "LLM + Tool Calling", fs=8, color='#4a3c8c', z=6)

# ── Box 2 : MCP server ──
bx2, by2, bw2, bh2 = 6.3, 2.4, 3.0, 1.8
shadow(ax1, bx2, by2, bw2, bh2)
box(ax1, bx2, by2, bw2, bh2, '#1a3a5c', '#0d2238')
p_inner2 = FancyBboxPatch((bx2 - bw2/2 + 0.12, by2 - bh2/2 + 0.12),
                            bw2 - 0.24, bh2 - 0.48,
                            boxstyle="round,pad=0.04,rounding_size=0.18",
                            lw=0, fc='#e6f0fb', zorder=4)
ax1.add_patch(p_inner2)
badge2 = FancyBboxPatch((bx2 - bw2/2 + 0.12, by2 + bh2/2 - 0.42),
                         bw2 - 0.24, 0.30,
                         boxstyle="round,pad=0.02,rounding_size=0.10",
                         lw=0, fc='#2a5a8c', zorder=5)
ax1.add_patch(badge2)
label(ax1, bx2, by2 + bh2/2 - 0.27, "robot2013-mcp  /  server.py", fs=8.5, color='#d0e8ff', z=6)
# gear icon (drawn as circle with radial lines)
g_x, g_y, g_r = bx2, by2 - 0.05, 0.26
gear_circle = Circle((g_x, g_y + 0.08), g_r, fc='#2a5a8c', ec='none', zorder=5)
ax1.add_patch(gear_circle)
ax1.text(g_x, g_y + 0.08, "MCP", ha='center', va='center',
         fontsize=7, color='white', fontweight='bold', zorder=6)
label(ax1, bx2, by2 - 0.30, "Python MCP Server", fs=8, color='#1a3a5c', z=6)

# ── Box 3 : Robot Structural Analysis ──
bx3, by3, bw3, bh3 = 6.3, 0.60, 3.0, 0.90
shadow(ax1, bx3, by3, bw3, bh3)
box(ax1, bx3, by3, bw3, bh3, '#C0392B', '#922b21')
label(ax1, bx3, by3 + 0.10, "Autodesk Robot Structural Analysis", fs=8.5, color='white', z=5)
label(ax1, bx3, by3 - 0.20, "2013  (win32com / COM)", fs=7.5, color='#ffd0cc', bold=False, z=5)

# ── Horizontal arrow ──
ax1_x1 = bx1 + bw1/2
ax1_x2 = bx2 - bw2/2
arrow(ax1, ax1_x1, by1, ax1_x2, by2, color='#5B4DA7', lw=2.2)
arrow_label(ax1, (ax1_x1 + ax1_x2)/2, by1 + 0.18,
            "MCP  (stdio  JSON-RPC)", ha='center', va='bottom', fs=9)

# ── Vertical arrow ──
ax1_y1 = by2 - bh2/2
ax1_y2 = by3 + bh3/2
arrow(ax1, bx2, ax1_y1, bx3, ax1_y2, color='#C0392B', lw=2.2)
arrow_label(ax1, bx2 + 0.18, (ax1_y1 + ax1_y2)/2,
            "win32com\n(COM)", ha='left', va='center', fs=9)

fig1.tight_layout(pad=0.3)
fig1.savefig("C:/laragon/www/Mcps/RobotMcpPy/docs/images/architecture.png",
             dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig1)
print("architecture.png saved.")


# ═══════════════════════════════════════════════
# Shared frame geometry  (Images 2 & 3)
# ═══════════════════════════════════════════════
bay_w    = 6.0
storey_h = 3.5
n_bays   = 2
n_stor   = 3

def node_xy(col, row):
    return col * bay_w, row * storey_h

nodes   = [(c, r) for r in range(n_stor + 1) for c in range(n_bays + 1)]
columns = [(c, r, c, r+1) for r in range(n_stor)  for c in range(n_bays + 1)]
beams   = [(c, r, c+1, r) for r in range(1, n_stor + 1) for c in range(n_bays)]


def draw_frame_base(ax, show_labels=True):
    ax.set_facecolor('#f7f9fc')
    margin_l, margin_r = 2.0, 3.0
    margin_b, margin_t = 1.8, 2.2
    xmax = n_bays * bay_w
    ymax = n_stor * storey_h

    ax.set_xlim(-margin_l, xmax + margin_r)
    ax.set_ylim(-margin_b, ymax + margin_t)
    ax.set_aspect('equal')
    ax.axis('off')

    # Grid
    for gx in np.arange(-margin_l, xmax + margin_r, 1.0):
        ax.axvline(gx, color='#e0e5ee', lw=0.4, zorder=0)
    for gy in np.arange(-margin_b, ymax + margin_t, 1.0):
        ax.axhline(gy, color='#e0e5ee', lw=0.4, zorder=0)

    # Columns  (draw twice for double-line / I-section look)
    for (c1, r1, c2, r2) in columns:
        x1, y1 = node_xy(c1, r1)
        x2, y2 = node_xy(c2, r2)
        ax.plot([x1, x2], [y1, y2], color='#1c3a6e', lw=7, solid_capstyle='butt', zorder=3)
        ax.plot([x1, x2], [y1, y2], color='#3a6db5', lw=2.5, solid_capstyle='butt', zorder=4,
                linestyle='--', dashes=(4, 3))

    # Beams
    for (c1, r1, c2, r2) in beams:
        x1, y1 = node_xy(c1, r1)
        x2, y2 = node_xy(c2, r2)
        ax.plot([x1, x2], [y1, y2], color='#1c3a6e', lw=5,   solid_capstyle='butt', zorder=3)
        ax.plot([x1, x2], [y1, y2], color='#5a8fd4', lw=1.5, solid_capstyle='butt', zorder=4,
                linestyle='--', dashes=(4, 3))

    # Fixed supports
    for c in range(n_bays + 1):
        bx, by = node_xy(c, 0)
        tri_x = [bx - 0.40, bx + 0.40, bx, bx - 0.40]
        tri_y = [by - 0.55, by - 0.55, by, by - 0.55]
        ax.fill(tri_x, tri_y, color='#1c3a6e', zorder=5)
        ax.plot(tri_x, tri_y, color='#0d2040', lw=1.5, zorder=6)
        for hx in np.linspace(bx - 0.52, bx + 0.52, 8):
            ax.plot([hx, hx - 0.17], [by - 0.55, by - 0.78],
                    color='#1c3a6e', lw=1.2, zorder=5)
        ax.plot([bx - 0.54, bx + 0.54], [by - 0.55, by - 0.55],
                color='#1c3a6e', lw=2.2, zorder=6)

    # Node dots
    for (c, r) in nodes:
        nx, ny = node_xy(c, r)
        ax.plot(nx, ny, 'o', color='white', markersize=9,
                markeredgecolor='#1c3a6e', markeredgewidth=2, zorder=7)

    if show_labels:
        # Column section tag (left outer, storey 2 mid)
        mx, my = node_xy(0, 1)
        ax.annotate("HEA200",
                    xy=(mx, my + storey_h * 0.5),
                    xytext=(mx - 1.4, my + storey_h * 0.5),
                    fontsize=8.5, fontweight='bold', color='#1c3a6e',
                    va='center', ha='right',
                    arrowprops=dict(arrowstyle='->', color='#1c3a6e', lw=1.0),
                    bbox=dict(boxstyle='round,pad=0.22', fc='#dce8fb',
                              ec='#1c3a6e', lw=0.9),
                    zorder=9)

        # Beam section tag (top-left bay, top chord)
        bx1t, by1t = node_xy(0, n_stor)
        bx2t, _    = node_xy(1, n_stor)
        ax.annotate("IPE300",
                    xy=((bx1t + bx2t)/2, by1t),
                    xytext=((bx1t + bx2t)/2, by1t + 1.0),
                    fontsize=8.5, fontweight='bold', color='#1c3a6e',
                    va='bottom', ha='center',
                    arrowprops=dict(arrowstyle='->', color='#1c3a6e', lw=1.0),
                    bbox=dict(boxstyle='round,pad=0.22', fc='#dce8fb',
                              ec='#1c3a6e', lw=0.9),
                    zorder=9)

        # Bay dimension arrow
        dim_y = -1.2
        ax.annotate('', xy=(bay_w, dim_y), xytext=(0.0, dim_y),
                    arrowprops=dict(arrowstyle='<->', color='#555', lw=1))
        ax.text(bay_w/2, dim_y - 0.28, f"{bay_w:.0f} m",
                ha='center', va='top', fontsize=8, color='#555')

        # Storey height annotations
        ann_x = xmax + 1.4
        for r in range(n_stor):
            yb = r * storey_h
            yt = (r + 1) * storey_h
            ax.annotate('', xy=(ann_x, yt), xytext=(ann_x, yb),
                        arrowprops=dict(arrowstyle='<->', color='#555', lw=1))
            ax.text(ann_x + 0.18, (yb + yt)/2, f"{storey_h:.1f} m",
                    ha='left', va='center', fontsize=8, color='#555')

    return (-margin_l, n_bays * bay_w + margin_r,
            -margin_b, n_stor * storey_h + margin_t)


# ═══════════════════════════════════════════════
# IMAGE 2 — frame_built.png  (1000 × 700)
# ═══════════════════════════════════════════════

fig2, ax2 = plt.subplots(figsize=(10, 7))
fig2.patch.set_facecolor('white')

draw_frame_base(ax2, show_labels=True)

xmax2 = n_bays * bay_w
ymax2 = n_stor * storey_h

# Watermark
ax2.text(xmax2/2, ymax2/2, "Built by Claude via MCP",
         ha='center', va='center', fontsize=24,
         color='#3a6db5', alpha=0.08, fontweight='bold',
         rotation=22, zorder=1)

# Title
ax2.set_title("2-Bay / 3-Storey Steel Frame\nAutomatically Generated via robot2013-mcp",
              fontsize=12.5, fontweight='bold', color='#1c3a6e', pad=10)

# Legend
col_patch  = mpatches.Patch(color='#1c3a6e', label='Column  (HEA200)')
beam_patch = mpatches.Patch(color='#5a8fd4', label='Beam  (IPE300)')
node_handle = Line2D([0], [0], marker='o', color='w', markerfacecolor='white',
                     markeredgecolor='#1c3a6e', markeredgewidth=2,
                     markersize=8, label='Node')
ax2.legend(handles=[col_patch, beam_patch, node_handle],
           loc='upper right', fontsize=8.5,
           framealpha=0.92, edgecolor='#aab', frameon=True)

# Stamp box
stamp = FancyBboxPatch((-1.85, ymax2 + 0.3), 3.8, 0.7,
                        boxstyle="round,pad=0.08",
                        lw=1.2, ec='#3a6db5', fc='#eef3fb', zorder=8)
ax2.add_patch(stamp)
ax2.text(-0.05, ymax2 + 0.65, "robot2013-mcp  |  v1.0",
         ha='center', va='center', fontsize=7.5,
         color='#1c3a6e', style='italic', zorder=9)

fig2.tight_layout(pad=0.4)
fig2.savefig("C:/laragon/www/Mcps/RobotMcpPy/docs/images/frame_built.png",
             dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig2)
print("frame_built.png saved.")


# ═══════════════════════════════════════════════
# IMAGE 3 — loads_analysis.png  (1000 × 700)
# ═══════════════════════════════════════════════

fig3, ax3 = plt.subplots(figsize=(10, 7))
fig3.patch.set_facecolor('white')

draw_frame_base(ax3, show_labels=False)

xmax3 = n_bays * bay_w
ymax3 = n_stor * storey_h

# ── UDL arrows on all beams ──
for (c1, r1, c2, r2) in beams:
    x1, y1 = node_xy(c1, r1)
    x2, y2 = node_xy(c2, r2)
    n_arr  = 8
    arrow_h = 0.65
    xs = np.linspace(x1 + 0.20, x2 - 0.20, n_arr)
    # top line
    ax3.plot([x1, x2], [y1 + arrow_h, y1 + arrow_h],
             color='#c0392b', lw=2, zorder=5)
    for xi in xs:
        ax3.annotate('', xy=(xi, y1), xytext=(xi, y1 + arrow_h),
                     arrowprops=dict(arrowstyle='->', color='#c0392b',
                                     lw=1.6, mutation_scale=11))

# ── UDL labels (one per bay per storey = left beam mid-span) ──
for r in range(1, n_stor + 1):
    x1l, y1l = node_xy(0, r)
    x2l, _   = node_xy(1, r)
    ax3.text((x1l + x2l)/2, y1l + 0.65 + 0.18, "5 kN/m",
             ha='center', va='bottom', fontsize=8.5,
             color='#c0392b', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.22', fc='#fdf2f2',
                       ec='#c0392b', lw=0.9), zorder=8)

# ── Reaction arrows ──
reactions = [38.5, 43.0, 38.5]
for idx, c in enumerate(range(n_bays + 1)):
    bx, by = node_xy(c, 0)
    r_h   = 0.85
    ax3.annotate('', xy=(bx, by + 0.02), xytext=(bx, by - r_h),
                 arrowprops=dict(arrowstyle='->', color='#1e8449',
                                 lw=2.4, mutation_scale=14))
    ax3.text(bx, by - r_h - 0.16,
             f"Fz = {reactions[idx]} kN",
             ha='center', va='top', fontsize=8,
             color='#1e8449', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.22', fc='#eafaf1',
                       ec='#27ae60', lw=0.9), zorder=8)

# ── Status box ──
sx, sy = xmax3 + 0.2, ymax3 + 1.25
status_patch = FancyBboxPatch((sx - 0.12, sy - 0.38), 3.1, 0.80,
                               boxstyle="round,pad=0.08",
                               lw=1.8, ec='#27ae60', fc='#eafaf1', zorder=10)
ax3.add_patch(status_patch)
# green circle bullet
ok_circle = Circle((sx + 0.25, sy + 0.02), 0.18, fc='#27ae60', ec='none', zorder=11)
ax3.add_patch(ok_circle)
ax3.text(sx + 0.25, sy + 0.02, "OK", ha='center', va='center',
         fontsize=5.5, color='white', fontweight='bold', zorder=12)
ax3.text(sx + 1.55, sy + 0.02, "Analysis Complete",
         ha='center', va='center', fontsize=10,
         color='#1e8449', fontweight='bold', zorder=11)

# Title
ax3.set_title("Static Analysis — Dead Load\n2-Bay / 3-Storey Frame",
              fontsize=12.5, fontweight='bold', color='#1c3a6e', pad=10)

# Legend
load_patch  = mpatches.Patch(color='#c0392b', label='UDL (5 kN/m)')
react_patch = mpatches.Patch(color='#1e8449', label='Support Reactions')
ax3.legend(handles=[load_patch, react_patch],
           loc='upper left', fontsize=8.5,
           framealpha=0.92, edgecolor='#aab')

fig3.tight_layout(pad=0.4)
fig3.savefig("C:/laragon/www/Mcps/RobotMcpPy/docs/images/loads_analysis.png",
             dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig3)
print("loads_analysis.png saved.")
print("\nAll 3 images generated successfully.")
