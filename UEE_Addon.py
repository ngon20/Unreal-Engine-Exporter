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

class AnimationExportPanel(bpy.types.Panel):
    bl_idname = 'UEE_PT_ANIMEXPORTPANEL'
    bl_label = 'Animation Export'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Unreal Export'

    def draw(self, context):
        layout = self.layout

        row = layout.row()

        row.operator('object.batch_export')




# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------
class UEE_OT_BatchExportBtn(bpy.types.Operator):
    bl_label = 'Batch Export'
    bl_idname = 'object.batch_export'
    

    def execute(self, context):
        print('\n\n\nN_GON: RUNNING UNREAL BATCH ANIMATION EXPORT SCRIPT!')
        mytool = bpy.context.window_manager.my_tool

        objects = bpy.data.objects
        exportList = []
        print(objects[0])

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

        print('N_GON: EXPORTING THE FOLLOWING RIG OBJECTS...')
        for export in exportList:
            print(export.name)

        #export!
        activeScene = bpy.context.window.scene

        for export in exportList:
            bpy.context.window.scene = export.users_scene[0]
            export.name = "rig"
            export.data.name = "rig"
            
            op.filepath = mytool.UEE_ExportPath + mytool.UEE_ExportName + '_' + export.users_scene[0].name + '.fbx'
            kwargs = op.__dict__
            
            bpy.ops.export_scene.fbx(**kwargs)
            
            export.name = "rig_" + export.users_scene[0].name
            export.data.name = "rig_" + export.users_scene[0].name
            
        bpy.context.window.scene = activeScene

        return {'FINISHED'}


# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------
classes = (
    UEE_Properties,
    ExportSettingsPanel,
    AnimationExportPanel,
    UEE_OT_BatchExportBtn
)

def menu_func(self, context):
    self.layout.operator(ExportPanel.bl_idname)

def register():
    print("\n ------------------------------------------------------------------------\n     Registering UEE\n ------------------------------------------------------------------------")
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.WindowManager.my_tool = PointerProperty(type=UEE_Properties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.WindowManager.my_tool
    

if __name__ == "__main__":
    register()  