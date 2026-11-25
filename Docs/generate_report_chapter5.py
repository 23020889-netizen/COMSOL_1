import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def build_chapter5_report():
    docs_dir = r"C:\Users\minht\OneDrive\Máy tính\Study\CNVCDT\COMSOL_1\Docs"
    comsol_dir = r"C:\Users\minht\OneDrive\Máy tính\Study\CNVCDT\COMSOL_1\Code\comsol"
    verif_dir = r"C:\Users\minht\OneDrive\Máy tính\Study\CNVCDT\COMSOL_1\Code\verification"
    root_dir = r"C:\Users\minht\OneDrive\Máy tính\Study\CNVCDT"

    out_docx = os.path.join(docs_dir, "Bao_Cao_Chuong_5_Mo_Phong_COMSOL_v2_full.docx")

    doc = docx.Document()
    for sec in doc.sections:
        sec.top_margin = Inches(0.95)
        sec.bottom_margin = Inches(0.95)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(0.9)
        sec.page_width = Inches(8.27)
        sec.page_height = Inches(11.69)

    NAVY = RGBColor(16, 54, 115)
    TEAL = RGBColor(15, 118, 110)
    TEXT = RGBColor(30, 41, 59)
    MUTED = RGBColor(71, 85, 105)

    def set_bg(cell, hx):
        cell._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hx}"/>'))

    def set_pad(cell, t=100, b=100, l=120, r=120):
        cell._tc.get_or_add_tcPr().append(parse_xml(
            f'<w:tcMar {nsdecls("w")}><w:top w:w="{t}" w:type="dxa"/><w:bottom w:w="{b}" w:type="dxa"/>'
            f'<w:left w:w="{l}" w:type="dxa"/><w:right w:w="{r}" w:type="dxa"/></w:tcMar>'))

    def set_borders(tbl, color="CBD5E1"):
        tbl._tbl.tblPr.append(parse_xml(
            f'<w:tblBorders {nsdecls("w")}>'
            f'<w:top w:val="single" w:sz="6" w:space="0" w:color="103673"/>'
            f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="103673"/>'
            f'<w:left w:val="none"/><w:right w:val="none"/>'
            f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
            f'<w:insideV w:val="none"/></w:tblBorders>'))

    def h1(txt):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(txt)
        r.bold = True; r.font.name = "Times New Roman"; r.font.size = Pt(14.5); r.font.color.rgb = NAVY
        return p

    def h2(txt):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(11)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(txt)
        r.bold = True; r.font.name = "Times New Roman"; r.font.size = Pt(12.5); r.font.color.rgb = NAVY
        return p

    def h3(txt):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(txt)
        r.bold = True; r.font.name = "Times New Roman"; r.font.size = Pt(11.5); r.font.color.rgb = TEAL
        return p

    def body(txt, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.18
        r = p.add_run(txt)
        r.font.name = "Times New Roman"; r.font.size = Pt(11); r.font.color.rgb = TEXT
        r.bold = bold; r.italic = italic
        return p

    def bullet(lead, rest):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        r1 = p.add_run("• " + lead + " ")
        r1.bold = True; r1.font.name = "Times New Roman"; r1.font.size = Pt(11); r1.font.color.rgb = TEXT
        r2 = p.add_run(rest)
        r2.font.name = "Times New Roman"; r2.font.size = Pt(11); r2.font.color.rgb = TEXT
        return p

    def eq(txt):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(5)
        r = p.add_run(txt)
        r.italic = True; r.font.name = "Times New Roman"; r.font.size = Pt(11); r.font.color.rgb = NAVY
        return p

    def add_table(caption, headers, rows, widths, center_cols=None):
        if center_cols is None:
            center_cols = set(range(1, len(headers)))
        pc = doc.add_paragraph()
        pc.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pc.paragraph_format.space_before = Pt(8)
        pc.paragraph_format.space_after = Pt(3)
        pc.paragraph_format.keep_with_next = True
        rc = pc.add_run(caption)
        rc.bold = True; rc.font.name = "Times New Roman"; rc.font.size = Pt(10.5); rc.font.color.rgb = NAVY

        tbl = doc.add_table(rows=1, cols=len(headers))
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        set_borders(tbl)

        for i, h in enumerate(headers):
            c = tbl.rows[0].cells[i]
            c.width = Inches(widths[i])
            set_bg(c, "103673")
            set_pad(c, 100, 100, 90, 90)
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)
            r = p.add_run(h)
            r.bold = True; r.font.name = "Times New Roman"; r.font.size = Pt(9.5); r.font.color.rgb = RGBColor(255, 255, 255)

        for r_idx, row in enumerate(rows):
            rcells = tbl.add_row().cells
            bg = "F1F5F9" if r_idx % 2 == 1 else "FFFFFF"
            for c_idx, val in enumerate(row):
                c = rcells[c_idx]
                c.width = Inches(widths[c_idx])
                set_bg(c, bg)
                set_pad(c, 75, 75, 90, 90)
                p = c.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in center_cols else WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)
                r = p.add_run(val)
                r.font.name = "Times New Roman"; r.font.size = Pt(9.5); r.font.color.rgb = TEXT
                if c_idx == 0:
                    r.bold = True

        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0); sp.paragraph_format.space_after = Pt(6)

    def add_fig(path, caption, w=6.0):
        if not os.path.exists(path):
            body(f"[Thiếu ảnh: {path}]", italic=True)
            return
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(path, width=Inches(w))

        pc = doc.add_paragraph()
        pc.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pc.paragraph_format.space_before = Pt(1)
        pc.paragraph_format.space_after = Pt(9)
        r = pc.add_run(caption)
        r.italic = True; r.font.name = "Times New Roman"; r.font.size = Pt(9.5); r.font.color.rgb = MUTED

    # =========================================================================
    # CHAPTER 5 CONTENT
    # =========================================================================
    h1("5. MÔ PHỎNG CON QUAY VI CƠ DẠNG ÂM THOA KÉP TRONG COMSOL MULTIPHYSICS 6.3")

    h2("5.1. Giới thiệu")
    body(
        "Trong khuôn khổ báo cáo này, nhóm thực hiện xây dựng và mô phỏng con quay vi cơ dạng âm thoa kép "
        "(Double Tuning Fork Gyroscope – TFG) sử dụng bộ dẫn động lược răng (comb-drive) trên phần mềm COMSOL Multiphysics 6.3. "
        "Cấu trúc âm thoa kép gồm hai nhánh đối xứng dao động ngược pha nhau theo phương kích thích, giúp triệt tiêu nhiễu chế độ chung "
        "(common-mode), giảm tổn hao năng lượng ra mỏ neo (anchor loss) và nâng cao độ nhạy nhờ đo vi sai."
    )
    body(
        "Để đánh giá định lượng hiệu quả của giải pháp khuếch đại cơ học, mô hình được xây dựng song song cho hai phương án "
        "trên cùng một diện tích chip, cùng khối lượng Coriolis và cùng điều kiện vật liệu/môi trường:"
    )
    bullet("Scheme I (Mô hình đề xuất có khuếch đại Chevron):",
           "Tích hợp cặp cơ cấu khuếch đại dịch chuyển hình thoi góc nghiêng α = 18° (tỉ số đòn bẩy lý thuyết R = 0,5·cot(18°) = 1,5388) "
           "giữa hai khung tách cảm ứng, đẩy hai khung cảm ứng sau khuếch đại di chuyển ngược pha theo trục y.")
    bullet("Scheme II (Mô hình truyền thống đối chứng):",
           "Loại bỏ cơ cấu khuếch đại Chevron, thay bằng cấu trúc hình thoi ghép nối cảm ứng (góc 38°) có lò xo neo ở giữa; "
           "các điện cực cảm ứng được đặt trực tiếp lên hai khung tách cảm ứng theo trục x.")

    h2("5.2. Bố trí và chức năng các thành phần")
    body(
        "Cấu trúc con quay được thiết kế đối xứng hoàn toàn qua cả trục x và trục y. Toàn bộ phần kết cấu chuyển động (rotor) "
        "được treo trên đế thông qua các mỏ neo cố định (Anchors), nối đất về 0 V. Vị trí và tên gọi các thành phần chính được thể hiện trên Hình 5.1."
    )
    add_fig(os.path.join(docs_dir, "So_Do_Bo_Tri_Thanh_Phan_Chinh_Con_Quay_MEMS_TFG_v2.png"),
            "Hình 5.1: Sơ đồ bố trí các thành phần chính của con quay âm thoa kép vi cơ (MEMS TFG) — Mô hình 3D COMSOL 6.3 mới (Scheme I Chevron).", w=6.2)

    bullet("Mỏ neo cố định & Chốt xoay trung tâm (Fixed & Pivot Anchors):", "Các điểm ngàm cố định kết cấu lên đế (Fixed Constraint), đóng vai trò làm điểm tựa cơ học và tiếp địa (GND = 0 V) cho toàn bộ rotor; chốt xoay trung tâm giữ trục quay cho hai đòn bẩy bập bênh.")
    bullet("Khối gia trọng trái/phải (m₁, m₂):", "Hai khối quán tính đối xứng (V_c = 0,1128 mm³, dày 40 µm) dao động ngược pha theo trục y ở chế độ Drive, sinh ra lực Coriolis dọc trục x khi có vận tốc góc Ω_z.")
    bullet("Khung dẫn động trái/phải (V₊, V₋) & Lò xo gấp:", "Chỉ cho phép chuyển động dọc trục y (L_d = 245 µm, rộng 8 µm), truyền lực đẩy–kéo tĩnh điện từ các điện cực răng lược vào hai khối gia trọng.")
    bullet("Đòn bẩy bập bênh trên/dưới (Top & Bottom Rockers):", "Hai thanh đòn nối đối xứng trên và dưới có chốt xoay ở giữa, ép hai khối Coriolis dao động ngược pha nhau theo trục y và đẩy mode đồng pha ra xa (16,8 kHz).")
    bullet("Khung cảm ứng bên (Sense) & Dầm uốn tách kênh (Flexure):", "Treo bởi lò xo L_s = 250 µm, cô lập chuyển động Drive theo trục y và chỉ truyền chuyển động Coriolis theo trục x vào vùng cảm ứng.")
    bullet("Cơ cấu khuếch đại Chevron (α = 18°, R = 1,53) & Khung khuếch đại trên/dưới (C₁, C₂):", "Biến đổi và khuếch đại dịch chuyển ngang (trục x) thành dịch chuyển dọc (trục y) tại hai khung khuếch đại trung tâm (V_af = 0,0320 mm³), nơi đo biến thiên điện dung vi sai.")

    h2("5.3. Thiết lập mô phỏng trong COMSOL Multiphysics 6.3")

    h3("5.3.1. Vật liệu và thông số hình học đồng nhất")
    body(
        "Để đảm bảo phép so sánh giữa Scheme I và Scheme II là công bằng tuyệt đối, cả hai mô hình được sinh tự động từ cùng một "
        "nguồn hình học tham số (tfg_geometry.py) và dùng chung một bộ thông số vật liệu Silicon đơn tinh thể đẳng hướng (Bảng 5.1) "
        "cùng các hệ số cản nhớt không khí theo Bảng 5 của bài báo tham chiếu (Bảng 5.2)."
    )

    add_table(
        "Bảng 5.1: Thông số vật liệu sử dụng đồng nhất cho cả hai Scheme trong COMSOL 6.3.",
        ["Thông số", "Ký hiệu", "Silicon (miền 3D cơ khí)", "Không khí (miền 2D tĩnh điện)", "Đơn vị"],
        [
            ["Mô-đun đàn hồi Young", "E", "170", "—", "GPa"],
            ["Hệ số Poisson", "ν", "0,22", "—", "—"],
            ["Khối lượng riêng", "ρ", "2320", "1,225", "kg/m³"],
            ["Hằng số điện môi tương đối", "ε_r", "11,7", "1,0", "—"],
        ],
        [2.1, 0.7, 1.3, 1.4, 0.8],
        center_cols={1, 2, 3, 4}
    )

    add_table(
        "Bảng 5.2: Thông số hình học và cản nhớt đồng bộ trong mô hình COMSOL 6.3.",
        ["Thông số thiết kế", "Ký hiệu", "Scheme I (Chevron)", "Scheme II (Truyền thống)", "Đơn vị"],
        [
            ["Chiều dày lớp cấu trúc", "h", "40", "40", "µm"],
            ["Thể tích mỗi khối Coriolis", "V_c", "0,1128", "0,1128", "mm³"],
            ["Thể tích khung dẫn động (2/nhánh)", "V_d", "0,0390", "0,0390", "mm³"],
            ["Thể tích khung tách cảm ứng", "V_s1", "0,0212", "0,0403", "mm³"],
            ["Thể tích khung khuếch đại", "V_s2", "0,0320", "—", "mm³"],
            ["Chiều dài lò xo (Drive / Sense / Phụ)", "L_d / L_s / L_a", "245 / 250 / 280", "245 / 250 / 290", "µm"],
            ["Bề rộng dầm lò xo", "w_s", "8", "8", "µm"],
            ["Góc nghiêng cơ cấu trung tâm", "α / θ", "18° (Chevron)", "38° (Hình thoi ghép)", "độ"],
            ["Hệ số cản trục Drive", "c_d", "2,61 × 10⁻⁵", "2,61 × 10⁻⁵", "N·s/m"],
            ["Hệ số cản trục Sense / Khuếch đại", "c_s1 / c_s2", "2,42 × 10⁻⁵ / 1,35 × 10⁻⁶", "2,42 × 10⁻⁵ / —", "N·s/m"],
        ],
        [2.2, 0.8, 1.3, 1.3, 0.7],
        center_cols={1, 2, 3, 4}
    )

    h3("5.3.2. Các giao diện vật lý (Physics Interfaces) và lưới chia")
    bullet("Component 1 (3D) – Solid Mechanics (solid):",
           "Giải bài toán cơ học chất rắn tuyến tính cho toàn bộ miền Silicon. Các mặt đáy mỏ neo được gán điều kiện ngàm cố định (Fixed Constraint), "
           "bỏ hoàn toàn ràng buộc Roller mặt đáy để phản ánh đúng kết cấu treo. Lưới sử dụng tam giác mặt đáy quét theo chiều dày (Sweep) với phần tử bậc 2 (serendipity), "
           "đạt 53.067 phần tử (Scheme I) và 54.202 phần tử (Scheme II) ở mức lưới chuẩn MESH_LEVEL = 2.")
    bullet("Component 2 (2D) – Electrostatics (es):",
           "Giải phương trình Poisson ∇·(ε∇V) = 0 cho hai ô đơn vị điện cực (ô lược dẫn động và ô tụ cảm ứng song song) nhằm xác định điện dung cơ bản "
           "(C₀ = 10,922 fF/ngón drive và 15,432 fF/điện cực sense).")
    bullet("Nhận dạng mode tự động theo vật lý:",
           "Thay vì gán cứng chỉ số nghiệm riêng, mô hình tính hệ số tham gia ngược pha P_drive (trục y) và P_sense (trục x) trên hai khối Coriolis để tự động phân biệt đúng hai chế độ làm việc.")

    h3("5.3.3. Sơ đồ đặt điện áp tại các điện cực (Drive & Sense) — Bổ sung mới")
    body(
        "Toàn bộ cấu trúc silicon chuyển động (rotor) được nối đất về GND = 0 V thông qua các mỏ neo. "
        "Cách đặt điện áp và cơ chế tạo lực/tín hiệu ra được thiết lập đồng nhất như Hình 5.2:"
    )
    add_fig(os.path.join(verif_dir, "voltage_scheme_I.png"),
            "Hình 5.2: Sơ đồ đặt điện áp đẩy–kéo (Push-Pull) tại các điện cực Drive và mạch khuếch đại điện tích vi sai tại các điện cực Sense.", w=6.0)

    bullet("Kênh dẫn động (Push–Pull Drive):",
           "Sử dụng 4 cụm lược stator đối xứng (N_d = 50 ngón/lược, h = 40 µm, khe hở g_d = 3 µm). "
           "Cụm D1 (trên-trái) và D4 (dưới-phải) đặt điện áp V_DC + V_AC·sin(ωt) = 20 + 5·sin(ωt) V; "
           "cụm D2 (dưới-trái) và D3 (trên-phải) đặt V_DC − V_AC·sin(ωt) = 20 − 5·sin(ωt) V. "
           "Do lực tĩnh điện F ∝ V², trên mỗi nhánh thành phần DC và bậc hai 2ω tự triệt tiêu, còn lại lực tuyến tính ngược pha:")
    eq("F_nhánh = ½·(dC/dy)·[(V_DC + v)² − (V_DC − v)²] = 2·(dC/dy)·V_DC·V_AC·sin(ωt) ≈ 2,361 µN")

    bullet("Kênh cảm ứng (Differential Sense & Charge Amplifier):",
           "Cả hai scheme sử dụng cùng N_s = 36 điện cực tụ song song (L_se = 80 µm, g_s = 3 µm, C₀ = ε₀·h·L_se/g_s ≈ 9,44 fF/tụ), "
           "chia đều thành hai nhánh vi sai S+ (khe giảm khi dịch chuyển dương) và S− (khe tăng). "
           "Hai nhánh nối vào đầu vào bộ khuếch đại điện tích vi sai với điện áp phân cực V_s = 5 V và tụ hồi tiếp C_f = 100 fF, cho điện áp ra:")
    eq("ΔC_diff = C(S+) − C(S−),       V_out = V_s · ΔC_diff / C_f")

    h2("5.4. Kết quả mô phỏng COMSOL 6.3 và đánh giá cải tiến")

    h3("5.4.1. Chế độ dao động riêng (Study 1: Eigenfrequency)")
    body(
        "Kết quả phân tích tần số riêng 3D trên COMSOL 6.3 cho thấy hai chế độ Drive và Sense tách biệt hoàn toàn về mặt vật lý. "
        "Trên Scheme I, chế độ Drive (Mode #1, f_d = 12.929,2 Hz) cho hai khối Coriolis dao động ngược pha dọc trục y kèm xoay hai đòn bẩy bập bênh, "
        "trong khi hai khung cảm ứng trung tâm đứng yên. Ở chế độ Sense (Mode #2, f_s = 13.080,9 Hz), hai khối Coriolis dao động ngược pha dọc trục x, "
        "nén/kéo cặp dầm Chevron để đẩy hai khung cảm ứng trung tâm di chuyển ngược pha mạnh theo trục y với tỉ số khuếch đại R_fem = 1,5285."
    )
    add_fig(os.path.join(comsol_dir, "MEMS_TFG_SchemeI_Chevron_v2_drive_mode.png"),
            "Hình 5.3: Dạng mode kích thích (Drive mode #1, f_d = 12.929,2 Hz) của Scheme I trên COMSOL 6.3.", w=5.6)
    add_fig(os.path.join(comsol_dir, "MEMS_TFG_SchemeI_Chevron_v2_sense_mode.png"),
            "Hình 5.4: Dạng mode cảm ứng (Sense mode #2, f_s = 13.080,9 Hz) của Scheme I trên COMSOL 6.3 — hai khung cảm ứng trung tâm khuếch đại ngược pha trục y.", w=5.6)
    add_fig(os.path.join(comsol_dir, "MEMS_TFG_SchemeII_Conventional_v2_sense_mode.png"),
            "Hình 5.5: Dạng mode cảm ứng (Sense mode #2, f_s = 13.116,4 Hz) của Scheme II truyền thống trên COMSOL 6.3.", w=5.6)

    h3("5.4.2. Đáp ứng tần số Hình 9 và biến thiên điện dung tại cộng hưởng (Study 3)")
    body(
        "Khi quét tần số quanh dải 11–15 kHz dưới tác dụng của cặp lực Coriolis thử nghiệm ±1 µN ngược pha (mục 5.3 bài báo), "
        "đáp ứng biên độ và biến thiên điện dung vi sai |ΔC_diff| tại đỉnh cộng hưởng được thể hiện trên Hình 5.6. "
        "Scheme I đạt biên độ đỉnh 1,2182 µm (sai lệch chỉ 0,26% so với 1,2214 µm của bài báo) và ΔC_diff = 138,07 fF, "
        "cao gấp 2,503 lần so với Scheme II truyền thống (0,4868 µm và 55,175 fF)."
    )
    add_fig(os.path.join(comsol_dir, "comparison_fig9.png"),
            "Hình 5.6: Đồ thị so sánh đáp ứng tần số (trái) và biến thiên điện dung vi sai |ΔC_diff| (phải) giữa Scheme I và Scheme II trên COMSOL 6.3.", w=6.1)
    add_fig(os.path.join(comsol_dir, "comparison_dC_diff.png"),
            "Hình 5.7: Đường cong biến thiên điện dung vi sai ΔC_diff(f) dưới lực thử ±1 µN — Scheme I đạt 138,07 fF (gấp 2,502 lần Scheme II: 55,18 fF).", w=6.0)

    h3("5.4.3. Phân tích tĩnh (Study 5) và vận hành con quay hoàn chỉnh (Study 4) — Bổ sung mới")
    body(
        "Trong phân tích tĩnh (Study 5) dưới lực ±1 µN theo trục cảm ứng, cơ cấu Chevron cho hệ số khuếch đại tĩnh R_fem = 1,4829 "
        "(so với lý thuyết 1,5388) và độ cứng ngược pha k_an = 4509,5 N/m, so với R_fem = 0,6078 và k_an = 2465,5 N/m của Scheme II."
    )
    body(
        "Trong mô phỏng vận hành con quay thực tế (Study 4), đặt lực đẩy–kéo từ điện áp Drive (F_drive = 2,361 µN) tại tần số f_drive "
        "và áp đặt lực Coriolis −2ρ(Ω × v) với vận tốc góc Ω_z = 1 rad/s: cả hai scheme đạt biên độ Drive gần như tương đương (~1,11 µm), "
        "nhưng Scheme I tạo ra biến thiên điện dung ΔC/Ω_z = 121,98 aF/(rad/s) và điện áp ra V_out/Ω_z = 6,0992 mV/(rad/s) [= 0,1065 mV/(°/s)], "
        "vượt trội 1,492 lần so với Scheme II (81,773 aF/(rad/s) và 4,0887 mV/(rad/s)). "
        "(Do độ lệch tần Δf ≈ 131–152 Hz ở trạng thái chưa khớp mode, khi tinh chỉnh điện áp khớp mode Δf → 0, tỉ số lợi ích sẽ tiến về giá trị cộng hưởng ~2,5×)."
    )
    add_fig(os.path.join(comsol_dir, "comparison_gyro_dC_Vout.png"),
            "Hình 5.8: Đặc tuyến tuyến tính của biến thiên điện dung ΔC_diff (trái) và điện áp đầu ra V_out (phải) theo tốc độ góc đầu vào Ω_z (0–300 °/s).", w=6.2)

    add_table(
        "Bảng 5.3: Tổng hợp toàn bộ kết quả mô phỏng thực tế trên COMSOL Multiphysics 6.3 (MESH_LEVEL = 2).",
        ["Đại lượng đánh giá", "Scheme I (Chevron)", "Scheme II (Truyền thống)", "Tỉ số (I / II)", "Tham chiếu bài báo"],
        [
            ["Tần số riêng Drive f_d (Hz)", "12.929,2", "12.985,7", "0,996×", "12.918,7 / 12.924,7"],
            ["Tần số riêng Sense f_s (Hz)", "13.080,9", "13.116,4", "0,997×", "13.043,1 / 13.100,6"],
            ["Độ tách tần số Δf = f_s − f_d (Hz)", "151,65", "130,73", "1,160×", "124,4 / 175,9"],
            ["Biên độ đỉnh Hình 9 (µm)", "1,2182", "0,4868", "2,503×", "1,2214 / 0,4833 (2,53×)"],
            ["Hệ số phẩm chất Q_sense", "1817", "1171", "1,552×", "—"],
            ["ΔC_diff tại đỉnh Hình 9 (fF)", "138,07", "55,175", "2,502×", "—"],
            ["Hệ số khuếch đại tĩnh R_fem", "1,4829", "0,6078", "2,440×", "1,53825 (Scheme I)"],
            ["Độ cứng ngược pha k_an (N/m)", "4509,5", "2465,5", "1,829×", "4598 / 2480"],
            ["Biên độ Drive tại f_d (µm)", "1,1135", "1,1080", "1,005×", "—"],
            ["ΔC / Ω_z vận hành thực (aF/(rad/s))", "121,98", "81,773", "1,492×", "—"],
            ["V_out / Ω_z vận hành thực (mV/(rad/s))", "6,0992", "4,0887", "1,492×", "—"],
        ],
        [2.0, 1.1, 1.2, 0.8, 1.2],
        center_cols={1, 2, 3, 4}
    )

    h2("5.5. Gợi ý cấu trúc trình bày trên Slide thuyết trình")
    body("Từ nội dung Chương 5 trên, bạn có thể bố trí gọn gàng thành 5–6 slide báo cáo:")
    bullet("Slide 1 – Kiến trúc & Nguyên lý đối chứng:", "Đặt Hình 5.1 ở trung tâm, nêu điểm khác biệt duy nhất giữa Scheme I (có Chevron 18° khuếch đại) và Scheme II (cảm ứng trực tiếp).")
    bullet("Slide 2 – Thiết lập đồng nhất trong COMSOL 6.3:", "Đưa Bảng 5.1 (Vật liệu đồng nhất) và tóm tắt lưới 53–54 nghìn phần tử, bỏ ràng buộc Roller mặt đáy.")
    bullet("Slide 3 – Sơ đồ đặt điện áp Drive & Sense:", "Đặt Hình 5.2 cùng 2 công thức lực đẩy–kéo (2,361 µN) và điện áp ra Charge Amplifier (V_out = V_s·ΔC_diff/C_f).")
    bullet("Slide 4 – Kết quả Mode Drive & Sense thực tế (kèm Animation GIF):", "Chèn trực tiếp 4 file ảnh động GIF (*_drive_mode.gif và *_sense_mode.gif trong Code/comsol/) hoặc ghép Hình 5.3–5.5 để trình diễn trực quan dao động ngược pha tách biệt giữa hai mode.")
    bullet("Slide 5 – Biến thiên điện dung ΔC & Hiệu năng vượt trội:", "Đặt Hình 5.7 (ΔC_diff), Hình 5.8 (V_out theo Ω_z) và Bảng 5.3 tóm tắt, nhấn mạnh tỉ số khuếch đại 2,50× ở cộng hưởng và 1,49× ở vận hành thực tế.")

    doc.save(out_docx)
    print("Saved:", out_docx)

if __name__ == "__main__":
    build_chapter5_report()
