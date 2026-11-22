from pathlib import Path

root = Path("android/app/src/main/java/com/nadadam/app")
root.mkdir(parents=True, exist_ok=True)

plugin = r'''package com.nadadam.app;

import android.content.ContentResolver;
import android.content.ContentValues;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "BackupStorage")
public class BackupStoragePlugin extends Plugin {
    @PluginMethod
    public void saveBackup(PluginCall call) {
        String fileName = call.getString("fileName");
        String content = call.getString("content");
        if (fileName == null || !fileName.matches("[\\\\p{L}\\\\p{N}_-]+\\\\.json") || content == null) {
            call.reject("نام یا محتوای فایل پشتیبان معتبر نیست.");
            return;
        }
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) {
            call.reject("ذخیره مستقیم در پوشه دانلودها به اندروید ۱۰ یا جدیدتر نیاز دارد.");
            return;
        }

        ContentResolver resolver = getContext().getContentResolver();
        String relativePath = Environment.DIRECTORY_DOWNLOADS + "/ندادم";
        Uri savedUri = null;
        try {
            String[] selectionArgs = new String[] { fileName, relativePath };
            resolver.delete(
                MediaStore.Downloads.EXTERNAL_CONTENT_URI,
                MediaStore.MediaColumns.DISPLAY_NAME + "=? AND " + MediaStore.MediaColumns.RELATIVE_PATH + "=?",
                selectionArgs
            );

            ContentValues values = new ContentValues();
            values.put(MediaStore.MediaColumns.DISPLAY_NAME, fileName);
            values.put(MediaStore.MediaColumns.MIME_TYPE, "application/json");
            values.put(MediaStore.MediaColumns.RELATIVE_PATH, relativePath);
            values.put(MediaStore.MediaColumns.IS_PENDING, 1);

            savedUri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (savedUri == null) throw new IllegalStateException("ساخت فایل در پوشه دانلودها ناموفق بود.");

            try (OutputStream output = resolver.openOutputStream(savedUri, "w")) {
                if (output == null) throw new IllegalStateException("امکان نوشتن فایل پشتیبان وجود ندارد.");
                output.write(content.getBytes(StandardCharsets.UTF_8));
                output.flush();
            }

            ContentValues ready = new ContentValues();
            ready.put(MediaStore.MediaColumns.IS_PENDING, 0);
            resolver.update(savedUri, ready, null, null);

            JSObject result = new JSObject();
            result.put("uri", savedUri.toString());
            result.put("fileName", fileName);
            result.put("folder", "Download/ندادم");
            call.resolve(result);
        } catch (Exception error) {
            if (savedUri != null) {
                try { resolver.delete(savedUri, null, null); } catch (Exception ignored) {}
            }
            call.reject("ذخیره فایل پشتیبان ناموفق بود: " + error.getMessage(), error);
        }
    }
}
'''
(root / "BackupStoragePlugin.java").write_text(plugin, encoding="utf-8")

activity = root / "MainActivity.java"
if not activity.exists():
    activity.write_text("""package com.nadadam.app;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(BackupStoragePlugin.class);
        super.onCreate(savedInstanceState);
    }
}
""", encoding="utf-8")
else:
    source = activity.read_text(encoding="utf-8")
    if "registerPlugin(BackupStoragePlugin.class)" not in source:
        source = source.replace(
            "public class MainActivity extends BridgeActivity {",
            "public class MainActivity extends BridgeActivity {\n    @Override\n    public void onCreate(Bundle savedInstanceState) {\n        registerPlugin(BackupStoragePlugin.class);\n        super.onCreate(savedInstanceState);\n    }\n",
            1
        )
        if "registerPlugin(BackupStoragePlugin.class)" not in source:
            raise SystemExit("Could not register BackupStoragePlugin in MainActivity.")
        if "import android.os.Bundle;" not in source:
            source = source.replace("package com.nadadam.app;", "package com.nadadam.app;\n\nimport android.os.Bundle;", 1)
        activity.write_text(source, encoding="utf-8")

print("Registered native MediaStore backup writer for Downloads/ندادم.")
