/* Offline GObject harness: only an OSK in squeekboard may change its layer. */
#include <glib-object.h>
#include <string.h>
typedef struct { GObject parent; guint layer; gchar *space; } PhoshLayerSurface;
typedef struct { GObjectClass parent; } PhoshLayerSurfaceClass;
G_DEFINE_TYPE(PhoshLayerSurface, phosh_layer_surface, G_TYPE_OBJECT)
static void get_property(GObject *o, guint id, GValue *v, GParamSpec *p) {
    (void)p; PhoshLayerSurface *s=(PhoshLayerSurface *)o;
    if (id==1) g_value_set_uint(v,s->layer); else g_value_set_string(v,s->space);
}
static void set_property(GObject *o, guint id, const GValue *v, GParamSpec *p) {
    (void)p; PhoshLayerSurface *s=(PhoshLayerSurface *)o;
    if(id==1) s->layer=g_value_get_uint(v); else {g_free(s->space);s->space=g_value_dup_string(v);}
}
static void finalize(GObject *o) {
    g_free(((PhoshLayerSurface *)o)->space);
    G_OBJECT_CLASS(phosh_layer_surface_parent_class)->finalize(o);
}
static void phosh_layer_surface_class_init(PhoshLayerSurfaceClass *klass) {
    GObjectClass *c=G_OBJECT_CLASS(klass);c->get_property=get_property;c->set_property=set_property;c->finalize=finalize;
    g_object_class_install_property(c,1,g_param_spec_uint("layer","layer","layer",0,3,2,G_PARAM_READWRITE));
    g_object_class_install_property(c,2,g_param_spec_string("namespace","namespace","namespace",NULL,G_PARAM_READWRITE));
}
static void phosh_layer_surface_init(PhoshLayerSurface *s) {s->layer=2;s->space=NULL;}
GType gtk_widget_get_type(void) {return G_TYPE_OBJECT;}
gboolean gtk_widget_get_mapped(gpointer object) {(void)object;return TRUE;}
gint gtk_widget_get_allocated_height(gpointer object) {(void)object;return 420;}
#include "../deploy/osk-overlay.c"
int main(int argc,char **argv) {
    gboolean target=argc==1;
    g_set_prgname(target?"squeekboard":"another-application");
    guint signal=g_signal_new("realize",G_TYPE_OBJECT,G_SIGNAL_RUN_FIRST,0,NULL,NULL,NULL,G_TYPE_NONE,0);
    gtk_module_init(&argc,&argv);
    PhoshLayerSurface *keyboard=g_object_new(phosh_layer_surface_get_type(),"namespace","osk",NULL);
    PhoshLayerSurface *panel=g_object_new(phosh_layer_surface_get_type(),"namespace","panel",NULL);
    GObject *ordinary=g_object_new(G_TYPE_OBJECT,NULL);
    g_signal_emit(keyboard,signal,0);g_signal_emit(panel,signal,0);g_signal_emit(ordinary,signal,0);
    g_assert_cmpuint(keyboard->layer,==,target?3:2);
    g_assert_cmpuint(panel->layer,==,2);
    keyboard->layer=2;g_signal_emit(keyboard,signal,0);
    g_assert_cmpuint(keyboard->layer,==,target?3:2);
    g_object_unref(keyboard);g_object_unref(panel);g_object_unref(ordinary);
    return 0;
}
