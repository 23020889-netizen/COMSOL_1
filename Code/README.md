# Code — mô hình COMSOL 6.3 con quay âm thoa MEMS (Scheme I chevron / Scheme II truyền thống)

Báo cáo chi tiết: [`../Docs/Bao_Cao_Sua_Mo_Hinh_COMSOL_TFG_v2.md`](../Docs/Bao_Cao_Sua_Mo_Hinh_COMSOL_TFG_v2.md)

## Thư mục
| Đường dẫn | Nội dung |
|---|---|
| `MEMS_Tuning_Fork_Gyroscope_*_Solved.mph` | 2 file **cũ** (giữ nguyên để đối chiếu; lỗi xem báo cáo mục 2) |
| `comsol/TFG_SchemeI_Chevron.java` | Bộ dựng + giải mô hình Scheme I cho COMSOL 6.3 (sinh tự động) |
| `comsol/TFG_SchemeII_Conventional.java` | Bộ dựng + giải mô hình Scheme II (cùng tham số, cùng tine) |
| `comsol/run_comsol_windows.bat`, `run_comsol_linux.sh` | Biên dịch + chạy cả hai, rồi so sánh |
| `generator/tfg_geometry.py` | Hình học tham số — nguồn duy nhất cho cả Java lẫn FEM kiểm chứng |
| `generator/tfg_physics.py` | Vật liệu, cản (Bảng 5), điện cực, điện áp — dùng chung 2 scheme |
| `generator/make_comsol_java.py` | Sinh 2 file Java |
| `generator/fe_check.py`, `fe_compare.py` | FEM độc lập (gmsh + scikit-fem) → `verification/` |
| `generator/analyze_old_mph.py` | Kiểm toán file .mph cũ (không cần COMSOL) |
| `generator/compare_comsol_runs.py` | Bảng/đồ thị so sánh sau khi chạy COMSOL |
| `generator/make_mode_gifs.py` | Ghép khung PNG theo pha thành GIF |
| `comsol/ExportMissingVisuals.java` | Xuất lại GIF/PNG từ .mph đã giải (sửa lỗi GIF duyệt qua mọi mode) |
| `verification/` | Kết quả kiểm chứng: mode, Hình 9, điện dung, sơ đồ điện áp, `results.json`, kiểm toán file cũ |

## Sinh file .mph mới (máy có COMSOL 6.3)
Windows: chạy `comsol\run_comsol_windows.bat` (sửa `COMSOL_BIN` nếu COMSOL không cài ở đường dẫn mặc định).

Linux/macOS:
```bash
cd Code/comsol && TFG_MESH=2 ./run_comsol_linux.sh
```
Thủ công:
```bash
comsol compile TFG_SchemeI_Chevron.java
```
```bash
comsol batch -inputfile TFG_SchemeI_Chevron.class -nosave
```
Thư mục xuất được ghi cứng vào Java (comsolbatch chặn biến môi trường): sinh lại bằng
`python3 make_comsol_java.py --outdir "D:/duong/dan/Code/comsol"` nếu chạy trên máy khác.
Đổi `MESH_LEVEL` / `PAPER_RESOLUTION` ở đầu file Java nếu cần (lưới thô/thường/mịn; bước quét 0.1 Hz như bài báo).

Ảnh động mode: mỗi GIF là **một** mode dao động theo pha (Dynamic data extension) + 12 khung PNG
`*_phaseXXX.png`; ghép bằng `python generator/make_mode_gifs.py comsol`. Xuất lại từ .mph đã giải (không giải lại):
`comsolcompile ExportMissingVisuals.java` rồi `comsolbatch -inputfile ExportMissingVisuals.class -nosave`.

Đầu ra mỗi scheme: `MEMS_TFG_Scheme*_v2.mph`, `*_log.txt` (bảng mode, tần số, R, V_out…), `*_modes.csv`,
`*_drive_FRF.csv`, `*_sense_FRF_fig9.csv`, `*_gyro_operation.csv`, `*_electrostatic_cells.csv`, `*_summary.txt`, ảnh PNG.
Sau cùng `comparison_SchemeI_vs_SchemeII.md` + `comparison_fig9.png`.

## Sửa hình học / tham số
Sửa `generator/tfg_geometry.py` hoặc `tfg_physics.py`, rồi:
```bash
cd Code/generator && python3 tfg_geometry.py && python3 make_comsol_java.py && python3 fe_compare.py
```
(`pip install gmsh scikit-fem shapely matplotlib scipy` cho phần kiểm chứng.) Không sửa tay file Java.
