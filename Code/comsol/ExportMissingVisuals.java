import com.comsol.model.*;
import com.comsol.model.util.*;

public class ExportMissingVisuals {
  static final String DIR = "C:/Users/minht/OneDrive/M\u00e1y t\u00ednh/Study/CNVCDT/COMSOL_1/Code/comsol/";

  static void exportPng(Model m, String tag, String pg, String filename, int w, int h) {
    try {
      try { m.result().export().remove(tag); } catch (Exception e) {}
      m.result().export().create(tag, "Image");
      m.result().export(tag).set("sourceobject", pg);
      m.result().export(tag).set("pngfilename", DIR + filename);
      m.result().export(tag).set("size", "manual");
      m.result().export(tag).set("unit", "px");
      m.result().export(tag).set("width", w);
      m.result().export(tag).set("height", h);
      m.result().export(tag).set("antialias", "on");
      m.result().export(tag).run();
      System.out.println("Exported PNG: " + filename);
    } catch (Exception e) {
      System.out.println("PNG failed (" + filename + "): " + e.getMessage());
    }
  }

  static void exportGif(Model m, String tag, String pg, String filename) {
    try {
      try { m.result().export().remove(tag); } catch (Exception e) {}
      m.result().export().create(tag, "Animation");
      m.result().export(tag).set("plotgroup", pg);
      m.result().export(tag).set("target", "file");
      try { m.result().export(tag).set("type", "movie"); } catch (Exception e) {}
      try { m.result().export(tag).set("movietype", "gif"); } catch (Exception e) {}
      m.result().export(tag).set("giffilename", DIR + filename);
      try { m.result().export(tag).set("sweeptype", "dynamic"); } catch (Exception e) {}
      try { m.result().export(tag).set("maxframes", 24); } catch (Exception e) {}
      try { m.result().export(tag).set("fps", 15); } catch (Exception e) {}
      try { m.result().export(tag).set("repeat", "forever"); } catch (Exception e) {}
      try {
        m.result().export(tag).set("size", "manual");
        m.result().export(tag).set("unit", "px");
        m.result().export(tag).set("width", 1280);
        m.result().export(tag).set("height", 720);
      } catch (Exception e) {}
      m.result().export(tag).run();
      System.out.println("Exported GIF: " + filename);
    } catch (Exception e) {
      System.out.println("GIF failed (" + filename + "): " + e.getMessage());
      e.printStackTrace();
    }
  }

  static void processModel(String mphName, String pre) throws Exception {
    System.out.println("Loading " + mphName + " ...");
    Model m = ModelUtil.load("mdl_" + pre, DIR + mphName);

    // 1. Export Animations for Drive & Sense modes
    exportGif(m, "anim_drv_" + pre, "pg_drive", pre + "_drive_mode.gif");
    exportGif(m, "anim_sns_" + pre, "pg_sense", pre + "_sense_mode.gif");

    // 2. Export Electrostatic cell plot & dC / Gyro plots
    exportPng(m, "img_es_" + pre, "pg_es", pre + "_electrostatic_cells.png", 1600, 900);
    exportPng(m, "img_dC_" + pre, "pg_dC", pre + "_dC_diff.png", 1400, 900);
    exportPng(m, "img_gyro_" + pre, "pg_gyro", pre + "_gyro_Vout.png", 1400, 900);

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
