/* GTK3 module for the Pi's squeekboard 1.43 PhoshLayerSurface.
 * Only the keyboard's "osk" layer surface is raised above fullscreen windows.
 * No input, text, credentials or other windows are observed or modified.
 */
#include <glib-object.h>
#include <glib/gstdio.h>
#include <string.h>

/* Public GTK3 API; runtime GTK3 is already a dependency of squeekboard. */
extern GType gtk_widget_get_type(void);
extern gboolean gtk_widget_get_mapped(gpointer widget);
extern gint gtk_widget_get_allocated_height(gpointer widget);
static GWeakRef keyboard;
static gchar *geometry_path;

static gboolean report_geometry(gpointer unused)
{
    (void)unused;
    if (!geometry_path) return G_SOURCE_CONTINUE;
    GObject *object = g_weak_ref_get(&keyboard);
    gboolean visible = object && gtk_widget_get_mapped(object);
    gint height = visible ? gtk_widget_get_allocated_height(object) : 0;
    gchar timestamp[G_ASCII_DTOSTR_BUF_SIZE];
    g_ascii_dtostr(timestamp, sizeof timestamp, g_get_monotonic_time()/1000000.0);
    gchar *json = g_strdup_printf("{\"visible\":%s,\"height\":%d,\"updated\":%s}",
        visible ? "true" : "false", CLAMP(height, 0, 8192), timestamp);
    g_file_set_contents_full(geometry_path, json, -1, G_FILE_SET_CONTENTS_CONSISTENT, 0600, NULL);
    g_free(json);
    if (object) g_object_unref(object);
    return G_SOURCE_CONTINUE;
}

static void geometry_changed(GObject *object, gpointer data)
{
    (void)object; (void)data;
    report_geometry(NULL);
}

static void size_changed(GObject *object, gpointer allocation, gpointer data)
{
    (void)allocation;
    geometry_changed(object, data);
}

static gboolean raise_keyboard(GSignalInvocationHint *hint, guint count,
                               const GValue *values, gpointer data)
{
    (void)hint; (void)data;
    if (count == 0) return TRUE;
    GObject *object = g_value_get_object(&values[0]);
    GType type = g_type_from_name("PhoshLayerSurface");
    if (!object || !type || !g_type_is_a(G_OBJECT_TYPE(object), type)) return TRUE;
    GParamSpec *layer = g_object_class_find_property(G_OBJECT_GET_CLASS(object), "layer");
    GParamSpec *space = g_object_class_find_property(G_OBJECT_GET_CLASS(object), "namespace");
    if (!layer || !G_IS_PARAM_SPEC_UINT(layer) || !(layer->flags & G_PARAM_WRITABLE)
        || !space || !G_IS_PARAM_SPEC_STRING(space)) return TRUE;
    gchar *name = NULL;
    g_object_get(object, "namespace", &name, NULL);
    if (g_strcmp0(name, "osk") == 0) {
        /* zwlr_layer_shell_v1.layer.overlay = 3; lock surfaces remain above it. */
        g_object_set(object, "layer", 3u, NULL);
        g_weak_ref_set(&keyboard, object);
        if (!g_object_get_data(object, "gpt-pi-geometry-observed")) {
            g_object_set_data(object, "gpt-pi-geometry-observed", GINT_TO_POINTER(1));
            if (g_signal_lookup("map", G_OBJECT_TYPE(object)))
                g_signal_connect_after(object, "map", G_CALLBACK(geometry_changed), NULL);
            if (g_signal_lookup("unmap", G_OBJECT_TYPE(object)))
                g_signal_connect_after(object, "unmap", G_CALLBACK(geometry_changed), NULL);
            if (g_signal_lookup("size-allocate", G_OBJECT_TYPE(object)))
                g_signal_connect_after(object, "size-allocate", G_CALLBACK(size_changed), NULL);
        }
        report_geometry(NULL);
    }
    g_free(name);
    return TRUE;
}

void gtk_module_init(gint *argc, gchar ***argv)
{
    (void)argc; (void)argv;
    if (g_strcmp0(g_get_prgname(), "squeekboard") != 0) return;
    static gboolean initialized = FALSE;
    if (initialized) return;
    initialized = TRUE;
    g_weak_ref_init(&keyboard, NULL);
    const gchar *runtime = g_getenv("XDG_RUNTIME_DIR");
    if (runtime && g_path_is_absolute(runtime)) {
        gchar *directory = g_build_filename(runtime, "gpt-pi-osk", NULL);
        if (g_mkdir_with_parents(directory, 0700) == 0)
            geometry_path = g_build_filename(directory, "geometry.json", NULL);
        g_free(directory);
    }
    g_timeout_add_seconds(1, report_geometry, NULL);
    gpointer klass = g_type_class_ref(gtk_widget_get_type());
    guint signal = g_signal_lookup("realize", gtk_widget_get_type());
    if (signal) g_signal_add_emission_hook(signal, 0, raise_keyboard, NULL, NULL);
    g_type_class_unref(klass);
}
