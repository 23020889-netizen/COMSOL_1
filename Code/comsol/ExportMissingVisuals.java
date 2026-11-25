import com.comsol.model.*;
import com.comsol.model.util.*;
import java.util.*;

/**
 * Re-exports the mode animations / figures from the already SOLVED v2 .mph files (no re-solve).
 *
 * FIX (2026-11): the previous version used the Animation default "Stored solutions" sequence, so the
 * GIF stepped through ALL 28 eigenmodes (frame 1 = drive mode, then the out-of-plane z modes at
 * 18-45 kHz ...).  That is why the "sense" animation showed the masses tilting along z.
 * Now: (1) sequence type = Dynamic data extension (phase 0..360 deg of the ONE mode selected in the
 * plot group), (2) a fixed deformation scale for all frames, (3) 12 PNG phase frames as a fallback
 * (python ../generator/make_mode_gifs.py . assembles them into GIFs).
 *
 *   comsolcompile ExportMissingVisuals.java
 *   comsolbatch -inputfile ExportMissingVisuals.class -nosave
 */
public class ExportMissingVisuals {
  static final String DIR = "C:/Users/minht/OneDrive/M\u00e1y t\u00ednh/Study/CNVCDT/COMSOL_1/Code/comsol/";

  static void exportPng(Model m, String tag, String pg, String filename, int w, int h) {
    try {
      try { m.result().export().remove(tag); } catch (Exception e) {}
      m.result().export().create(tag, "Image");
      m.result().export(tag).set("sourceobject", pg);
      m.result().export(tag).set("pngfilename", DIR + filename);
      try {
        m.result().export(tag).set("size", "manual");
        m.result().export(tag).set("unit", "px");
        m.result().export(tag).set("width", w);
        m.result().export(tag).set("height", h);
        m.result().export(tag).set("antialias", "on");
      } catch (Exception e) {}
      m.result().export(tag).run();
      System.out.println("Exported PNG: " + filename);
    } catch (Exception e) {
      System.out.println("PNG failed (" + filename + "): " + e.getMessage());
    }
  }

  /** Fixed deformation scale: 150 um visual amplitude for the selected eigenmode. */
  static void fixDeformScale(Model m, String pg) {
    try {
      int level = m.result(pg).getIntArray("looplevel")[0];
      String ds = m.result(pg).getString("data");
      try { m.component("comp1").cpl().create("max_vis", "Maximum"); } catch (Exception e) {}
      m.component("comp1").cpl("max_vis").selection().all();
      String t = "gev_vis_" + pg;
      try { m.result().numerical().remove(t); } catch (Exception e) {}
      m.result().numerical().create(t, "EvalGlobal");
      m.result().numerical(t).set("data", ds);
      m.result().numerical(t).set("expr", new String[]{"comp1.max_vis(solid.disp)", "1", "1"});
      m.result().numerical(t).set("unit", new String[]{"um", "1", "1"});
      double[][] r = m.result().numerical(t).getReal();
      double dmax = (r.length == 3) ? r[0][level - 1] : r[level - 1][0];
      double scale = 150.0 / dmax;
      m.result(pg).feature("surf1").feature("def1").set("scaleactive", true);
      m.result(pg).feature("surf1").feature("def1").set("scale", scale);
      System.out.println(pg + ": mode " + level + ", max |u| = " + dmax + " um -> deformation scale " + scale);
    } catch (Exception e) {
      System.out.println("(fixed scale not set for " + pg + ": " + e.getMessage() + ")");
    }
  }

  static void exportGif(Model m, String tag, String pg, String base) {
    try {
      try { m.result().export().remove(tag); } catch (Exception e) {}
      m.result().export().create(tag, "Animation");
      m.result().export(tag).set("plotgroup", pg);
      m.result().export(tag).set("target", "file");
      m.result().export(tag).set("sweeptype", "dde");   // phase sweep of ONE mode (not all stored solutions!)
      try { m.result().export(tag).set("cycletype", "full"); } catch (Exception e) {}
      try { m.result().export(tag).set("type", "movie"); } catch (Exception e) {}
      try { m.result().export(tag).set("movietype", "gif"); } catch (Exception e) {}
      m.result().export(tag).set("giffilename", DIR + base + ".gif");
      try { m.result().export(tag).set("maxframes", 24); } catch (Exception e) {}
      try { m.result().export(tag).set("fps", 12); } catch (Exception e) {}
      try { m.result().export(tag).set("synchronize", true); } catch (Exception e) {}
      try { m.result().export(tag).set("repeat", "forever"); } catch (Exception e) {}
      try {
        m.result().export(tag).set("size", "manual");
        m.result().export(tag).set("unit", "px");
        m.result().export(tag).set("width", 1280);
        m.result().export(tag).set("height", 720);
      } catch (Exception e) {}
      m.result().export(tag).run();
      System.out.println("Exported GIF (phase sweep): " + base + ".gif");
    } catch (Exception e) {
      System.out.println("GIF failed (" + base + "): " + e.getMessage() + "  -> use the PNG phase frames");
    }
    // fallback: 12 phase frames
    try {
      for (int k = 0; k < 12; k++) {
        m.result(pg).set("phasetype", "manual");
        m.result(pg).set("phase", String.valueOf(30 * k));
        exportPng(m, tag + "_f" + k, pg, base + String.format(Locale.US, "_phase%03d.png", 30 * k), 1280, 720);
      }
      m.result(pg).set("phase", "0");
    } catch (Exception e) {
      System.out.println("phase frames failed: " + e.getMessage());
    }
  }

  static void processModel(String mphName, String pre) throws Exception {
    System.out.println("Loading " + mphName + " ...");
    Model m = ModelUtil.load("mdl_" + pre, DIR + mphName);
    fixDeformScale(m, "pg_drive");
    fixDeformScale(m, "pg_sense");
    exportGif(m, "anim_drv_" + pre, "pg_drive", pre + "_drive_mode");
    exportGif(m, "anim_sns_" + pre, "pg_sense", pre + "_sense_mode");
    exportPng(m, "img_drv_" + pre, "pg_drive", pre + "_drive_mode.png", 1600, 900);
    exportPng(m, "img_sns_" + pre, "pg_sense", pre + "_sense_mode.png", 1600, 900);
    exportPng(m, "img_es_" + pre, "pg_es", pre + "_electrostatic_cells.png", 1600, 900);
    exportPng(m, "img_dC_" + pre, "pg_dC", pre + "_dC_diff.png", 1400, 900);
    exportPng(m, "img_gyro_" + pre, "pg_gyro", pre + "_gyro_Vout.png", 1400, 900);
    m.save(DIR + mphName);
    ModelUtil.remove("mdl_" + pre);
    System.out.println("Finished " + pre);
  }

  public static void main(String[] args) {
    try {
      processModel("MEMS_TFG_SchemeI_Chevron_v2.mph", "MEMS_TFG_SchemeI_Chevron_v2");
      processModel("MEMS_TFG_SchemeII_Conventional_v2.mph", "MEMS_TFG_SchemeII_Conventional_v2");
    } catch (Exception e) {
      e.printStackTrace();
    }
  }
}
