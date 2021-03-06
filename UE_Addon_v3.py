bl_info = {
    "name": "Unreal Engine Exporter",
    "blender": (2, 80, 0),
    "category": "Import-Export",
}

import bpy
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       EnumProperty,
                       PointerProperty
                       )
from bpy.app.handlers import persistent
# ------------------------------------------------------------------------
#    Handlers
# ------------------------------------------------------------------------
#presave
@persistent
def UEE_SaveHandler(dummy):
    if bpy.data.objects.get('.UEE_EmptySerializer') is None:
        print('UEE: Creating Empty for Serialization')
        bpy.ops.scene.new(type='EMPTY')
        obj = bpy.data.objects.new(".UEE_EmptySerializer", None)
        obj.use_fake_user = True
        bpy.ops.scene.delete()

    obj = bpy.data.objects.get('.UEE_EmptySerializer')

    mytool = bpy.context.window_manager.my_tool
    myserializer = obj.my_serializer

    myserializer.UEE_ExportName = mytool.UEE_ExportName
    myserializer.UEE_ExportPath = mytool.UEE_ExportPath

#postload
@persistent
def UEE_LoadHandler(dummy):
    #If we have an EmptySerializer, update our windowmanager's properties to match our object's
    if bpy.data.objects.get('.UEE_EmptySerializer') is not None:
        obj = bpy.data.objects.get('.UEE_EmptySerializer')

        mytool = bpy.context.window_manager.my_tool
        myserializer = obj.my_serializer

        mytool.UEE_ExportName = myserializer.UEE_ExportName
        mytool.UEE_ExportPath = myserializer.UEE_ExportPath




# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------

class UEE_Properties(bpy.types.PropertyGroup):

    UEE_ExportName: StringProperty(
        name="Name",
        description="Choose a name for this/these object(s)",
        default="",
        maxlen=1024,
        )

    UEE_ExportPath: StringProperty(
        name = "Path",
        description="Choose where you would like to save this/these object(s)",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
        )

# ------------------------------------------------------------------------
#    User Interface
# ------------------------------------------------------------------------
class ExportSettingsPanel(bpy.types.Panel):
    bl_idname = 'UEE_PT_EXPORTSETTINGSPANEL'
    bl_label = 'Export Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Unreal Export'

    def draw(self, context):
        layout = self.layout
        mytool = bpy.context.window_manager.my_tool
        layout.prop(mytool, 'UEE_ExportName')
        layout.prop(mytool, 'UEE_ExportPath')

class SkeletonExportPanel(bpy.types.Panel):
    bl_idname = 'UEE_PT_SKEXPORTPANEL'
    bl_label = 'Skeleton Export'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Unreal Export'

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        layout.label(text='Exports Skeleton:')
        layout.operator('object.skeleton_export')

class AnimationExportPanel(bpy.types.Panel):
    bl_idname = 'UEE_PT_ANIMEXPORTPANEL'
    bl_label = 'Animation Export'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Unreal Export'

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        layout.label(text='Exports Animation:')
        layout.operator('object.batch_animation_export')
        layout.operator('object.single_animation_export')
# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------
class UEE_OT_SkeletonExportBtn(bpy.types.Operator):
    bl_label = 'Skeleton Export'
    bl_idname = 'object.skeleton_export'
    
    def execute(self, context):
        mytool = bpy.context.window_manager.my_tool

        if bpy.data.objects.get('rig') is None:
            raise Exception("No 'rig' object found.  Nothing was exported.")
        
        rig = bpy.data.objects.get('rig')
        bValid = False

        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                if obj.parent == rig:
                    bpy.ops.object.select_all(action='DESELECT')
                    rig.select_set(state=True)
                    obj.select_set(state=True)
                    bValid = True

        if (bValid == False):
            raise Exception("Rig found but no mesh is attached.  Nothing was exported.")

        #code from forums to store export parameters from preset to 'op'
        presetDirectory = bpy.utils.preset_paths('operator/export_scene.fbx/')
        presetPath = presetDirectory[0] + 'UE4_Skeleton.py'

        file = open(presetPath, 'r')
        class emptyclass(object):
            __slots__ = ('__dict__',)
        op = emptyclass()

        for line in file.readlines()[3::]:
            exec(line, globals(), locals())

        op.filepath = bpy.path.abspath(mytool.UEE_ExportPath) + mytool.UEE_ExportName + '.fbx'
        kwargs = op.__dict__
        print("------------------------------------------------------------------------\n     Exporting Rig:")
        print('    ' + rig.name)
        print('------------------------------------------------------------------------')

        bpy.ops.export_scene.fbx(**kwargs)

        return {'FINISHED'}


class UEE_OT_BatchExportBtn(bpy.types.Operator):
    bl_label = 'Batch Export'
    bl_idname = 'object.batch_animation_export'
    

    def execute(self, context):
        print('\n\n\nN_GON: RUNNING UNREAL BATCH ANIMATION EXPORT SCRIPT!')
        mytool = bpy.context.window_manager.my_tool

        objects = bpy.data.objects
        exportList = []

        #Populate exportList with all objects of type armature that's name begins with "rig"
        for obj in objects:
            if (obj.type == "ARMATURE"):
                if obj.name.lower().startswith("rig"):
                    #check if the rig is part of a scene.  If its not, that's because its the skeleton we're linked to which we dont export
                    #alternatively, it could be a lingering object that is no longer part of any scene which we also dont export...
                    if (len(obj.users_scene) > 0):
                        exportList.append(obj)
                    
        #Ensure there is only one armature named rig[...] per scene
        sceneList = []
        for export in exportList:
            sceneList.append(export.users_scene)

        if not (len(set(sceneList)) == len(sceneList)):
            raise Exception("Multiple Armatures with prefix 'rig' detected per scene.  Nothing was exported")
            
        #code from forums to store export parameters from preset to 'op'
        presetDirectory = bpy.utils.preset_paths('operator/export_scene.fbx/')
        presetPath = presetDirectory[0] + 'UE4_Animation.py'

        file = open(presetPath, 'r')
        class emptyclass(object):
            __slots__ = ('__dict__',)
        op = emptyclass()

        for line in file.readlines()[3::]:
            exec(line, globals(), locals())

        print("------------------------------------------------------------------------\n     Exporting Animations:")
        for export in exportList:
            print('    ' + export.name)
        print('------------------------------------------------------------------------')

        #export!
        activeScene = bpy.context.window.scene

        for export in exportList:
            bpy.context.window.scene = export.users_scene[0]
            export.name = "rig"
            export.data.name = "rig"
            
            op.filepath = bpy.path.abspath(mytool.UEE_ExportPath) + mytool.UEE_ExportName + '_' + export.users_scene[0].name + '.fbx'
            kwargs = op.__dict__
            
            bpy.ops.export_scene.fbx(**kwargs)
            
            export.name = "rig_" + export.users_scene[0].name
            export.data.name = "rig_" + export.users_scene[0].name
            
        bpy.context.window.scene = activeScene

        return {'FINISHED'}

class UEE_OT_SingleExportBtn(bpy.types.Operator):
    bl_label = 'Singular Export'
    bl_idname = 'object.single_animation_export'
    

    def execute(self, context):
        print('\n\n\nN_GON: RUNNING UNREAL SINGLE ANIMATION EXPORT SCRIPT!')
        mytool = bpy.context.window_manager.my_tool

        objects = bpy.context.scene.objects
        exportList = []

        for obj in objects:
            if (obj.type == "ARMATURE"):
                if obj.name.lower().startswith("rig"):
                    exportList.append(obj)

        if not len(exportList) == 1:
            raise Exception("Multiple armature objects with prefix 'rig' detected in scene.  Nothing was exported")
            
        #code from forums to store export parameters from preset to 'op'
        presetDirectory = bpy.utils.preset_paths('operator/export_scene.fbx/')
        presetPath = presetDirectory[0] + 'UE4_Animation.py'

        file = open(presetPath, 'r')
        class emptyclass(object):
            __slots__ = ('__dict__',)
        op = emptyclass()

        for line in file.readlines()[3::]:
            exec(line, globals(), locals())

        print("------------------------------------------------------------------------\n     Exporting Animation:")
        for export in exportList:
            print('    ' + export.name)
        print('------------------------------------------------------------------------')
        #export!
        exoirt = exportList[0]

        export.name = "rig"
        export.data.name = "rig"

        op.filepath = bpy.path.abspath(mytool.UEE_ExportPath) + mytool.UEE_ExportName + '_' + export.users_scene[0].name + '.fbx'
        kwargs = op.__dict__
            
        bpy.ops.export_scene.fbx(**kwargs)
            
        export.name = "rig_" + export.users_scene[0].name
        export.data.name = "rig_" + export.users_scene[0].name

        return {'FINISHED'}


# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------
classes = (
    UEE_Properties,
    ExportSettingsPanel,
    SkeletonExportPanel,
    AnimationExportPanel,
    UEE_OT_SkeletonExportBtn,
    UEE_OT_BatchExportBtn,
    UEE_OT_SingleExportBtn
)

def menu_func(self, context):
    self.layout.operator(ExportPanel.bl_idname)

def register():
    print("\n ------------------------------------------------------------------------\n     Registering UEE\n ------------------------------------------------------------------------")
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.WindowManager.my_tool = PointerProperty(type=UEE_Properties)
    bpy.types.Object.my_serializer = PointerProperty(type=UEE_Properties)

    bpy.app.handlers.save_pre.append(UEE_SaveHandler)
    bpy.app.handlers.load_post.append(UEE_LoadHandler)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.WindowManager.my_tool
    del bpy.types.Object.my_serializer

    bpy.app.handlers.save_pre.remove(UEE_SaveHandler)
    bpy.app.handlers.load_post.remove(UEE_LoadHandler)
    

if __name__ == "__main__":
    register()  
