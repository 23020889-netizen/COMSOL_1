"""Generate publication-grade LaTeX-styled annotated layout diagram for Scheme I (Chevron)."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image

# Configure LaTeX-style typography: Serif text + Computer Modern math
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['mathtext.fontset'] = 'cm'
plt.rcParams['axes.unicode_minus'] = False

SRC_IMG = r"C:\Users\minht\.gemini\antigravity\brain\d950ed5d-a166-42f5-a583-f881f868b3f0\scratch\cropped_3d.png"
OUT_DOCS = r"C:\Users\minht\OneDrive\Máy tính\Study\CNVCDT\COMSOL_1\Docs\So_Do_Bo_Tri_Thanh_Phan_Chinh_Con_Quay_MEMS_TFG_v2.png"
OUT_ART = r"C:\Users\minht\.gemini\antigravity\brain\d950ed5d-a166-42f5-a583-f881f868b3f0\So_Do_Bo_Tri_Thanh_Phan_Chinh_Con_Quay_MEMS_TFG_v2.png"


def main():
    img = Image.open(SRC_IMG)
    w, h = img.size  # 1580 x 930

    fig = plt.figure(figsize=(18, 11), dpi=250, facecolor='white')
    ax = fig.add_axes([0, 0, 1, 1], facecolor='white')
    ax.set_xlim(0, 1800)
    ax.set_ylim(0, 1100)
    ax.axis('off')

    # Academic LaTeX-style header
    ax.text(
        900, 1054,
        "SƠ ĐỒ BỐ TRÍ CÁC THÀNH PHẦN CHÍNH CỦA CON QUAY ÂM THOA VI CƠ (MEMS TFG)",
        ha='center', va='center', fontsize=18.5, fontweight='bold', color='#111827'
    )
    ax.text(
        900, 1018,
        r"Mô hình 3D COMSOL 6.3 — Cấu trúc Scheme I tích hợp cơ cấu khuếch đại Chevron ($\alpha = 18^\circ,\; R = 1.53$) và đòn bẩy bập bênh",
        ha='center', va='center', fontsize=13, style='italic', color='#374151'
    )

    # Image placement box
    x0, y0 = 285, 130
    box_w, box_h = 1230, 725

    frame = patches.FancyBboxPatch(
        (x0 - 10, y0 - 10), box_w + 20, box_h + 20,
        boxstyle="round,pad=0.25,rounding_size=8",
        linewidth=0.9, edgecolor='#CBD5E1', facecolor='white', zorder=1
    )
    ax.add_patch(frame)

    ax.imshow(img, extent=[x0, x0 + box_w, y0, y0 + box_h], aspect='auto', zorder=2)

    def pt(px, py):
        cx = x0 + (px / w) * box_w
        cy = y0 + ((h - py) / h) * box_h
        return (cx, cy)

    def callout(label, box_xy, target_px, color, ha='center'):
        tx, ty = pt(*target_px)
        bx, by = box_xy

        ax.annotate(
            "", xy=(tx, ty), xytext=(bx, by),
            arrowprops=dict(
                arrowstyle="-|>", color=color, lw=1.25,
                shrinkA=6, shrinkB=4, mutation_scale=11
            ),
            zorder=5
        )
        ax.scatter([tx], [ty], s=22, color=color, zorder=6)

        ax.text(
            bx, by, label,
            ha=ha, va='center', fontsize=11.5, fontweight='bold', color=color,
            bbox=dict(
                boxstyle='round,pad=0.38', facecolor='white',
                edgecolor=color, linewidth=1.0, alpha=0.97
            ),
            zorder=7
        )

    # Top row
    callout("Đòn bẩy bập bênh trên (Top Rocker)", (490, 945), (595, 295), "#B45309")
    callout(r"Khung khuếch đại trên ($C_1$)", (950, 945), (785, 395), "#0F766E")
    callout(r"Khung dẫn động phải ($V_-$)", (1490, 915), (975, 165), "#B91C1C")

    # Left side
    callout(r"Khung dẫn động trái ($V_+$)", (145, 775), (365, 445), "#B91C1C")
    callout(r"Khối gia trọng trái ($m_1$)", (145, 625), (490, 575), "#1D4ED8")
    callout("Mỏ neo cố định & Lò xo gấp", (145, 465), (195, 470), "#334155")
    callout("Khung cảm ứng bên trái (Sense)", (150, 300), (305, 635), "#4D7C0F")

    # Right side
    callout(r"Khối gia trọng phải ($m_2$)", (1645, 730), (1085, 290), "#1D4ED8")
    callout("Khung cảm ứng bên phải (Sense)", (1640, 565), (1345, 270), "#4D7C0F")
    callout("Dầm uốn tách kênh (Flexure)", (1645, 420), (1312, 312), "#0F766E")
    callout("Đòn bẩy bập bênh dưới (Bottom Rocker)", (1625, 265), (1160, 540), "#B45309")
    callout("Chốt xoay trung tâm (Pivot Anchor)", (1625, 130), (1095, 608), "#334155")

    # Bottom row
    callout(r"Cơ cấu khuếch đại Chevron ($\alpha = 18^\circ,\; R = 1.53$)", (615, 65), (845, 445), "#6D28D9")
    callout(r"Khung khuếch đại dưới ($C_2$)", (1185, 65), (900, 490), "#0F766E")

    os.makedirs(os.path.dirname(OUT_DOCS), exist_ok=True)
    plt.savefig(OUT_DOCS, dpi=250, bbox_inches='tight', facecolor='white')
    plt.savefig(OUT_ART, dpi=250, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print("Saved:", OUT_DOCS)
    print("Saved:", OUT_ART)


if __name__ == "__main__":
    main()
