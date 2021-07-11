bl_info = {
'name': 'Rigging Helper',
'author': 'Droillex',
'version': (0, 1),
'blender': (2, 80, 0),
'location': 'View3D',
'description': 'Some simple tools to speed up rigging process',
}

import bpy
from bpy.types import (Panel, Operator, PropertyGroup)
from bpy.props import (BoolProperty, PointerProperty, StringProperty, EnumProperty)
this = bpy.context

separator = ','

# Function to switch from proxy mesh to hi-res original one
def switch_proxies(mode = 'ORIG', proxy_suffix='Proxy', original_suffix='Orig'):
    conv = {'ORIG': True, 'PROXY': False}
    toOrigs = conv[mode]
    proxies = []
    origs = []

    # Find orig and proxy objects in current scene
    for object in this.scene.objects:
        splited = object.name.split('.')
        if proxy_suffix in splited:
            proxies.append(object)
            continue
        if original_suffix in splited:
            origs.append(object)
            continue

    # Switch to specified objects      
    for obj in proxies:
        obj.hide_set(toOrigs)
        obj.hide_viewport = toOrigs
        
    for obj in origs:
        obj.hide_set(not toOrigs)
        obj.hide_viewport = not toOrigs

        
# Transfer curve hooks from meta to retargeted rig
def transfer_hooks(target_state = True):
# Metarig object
    meta = 'demo_metarig'
    meta = this.scene.objects.get(meta)
    
# Generated rig object
    generated = 'demo_generated'
    generated = this.scene.objects.get(generated)
    
# If name contains 'Curve' Suffix
    for obj in [objs for objs in this.scene.objects if 'Curve' in objs.name.split('.')]:
        curve = obj
        # For every hook of selected curve
        for hook in [x for x in curve.modifiers if x.type == 'HOOK']:
        
            isRetargeted = 'generated' in hook.name
            
            if isRetargeted == target_state:
                continue
#           Switch hook target    
            if isRetargeted:
                hook.object = meta
                hook.name = hook.name.replace('_generated', '')
                continue
            
            hook.object = generated
            hook.name += '_generated'


# Transfer vertex groups with weights from one object to another
def transfer_weights(obj_from, obj_to, method):
    this = bpy.context

    source = this.scene.objects.get(obj_from)
    target = this.scene.objects.get(obj_to)

    target.hide_set(False)
    target.hide_viewport = False

    source.hide_set(False)
    source.hide_viewport = False
    
#    Disable armature modifier if enabled

    if 'Armature' in target.modifiers:
        target.modifiers['Armature'].show_viewport = False
    if 'Armature' in source.modifiers:
        source.modifiers['Armature'].show_viewport = False
        
#   Add 'data transfer' modifier, set specified settings

    data_transfer = target.modifiers.new(type = 'DATA_TRANSFER', name = 'Data Transfer')

    data_transfer.object = source

    data_transfer.use_vert_data = True
    data_transfer.data_types_verts = {'VGROUP_WEIGHTS'}
    data_transfer.vert_mapping = method

#   Move modifier up, apply changes 
    
    bpy.ops.object.modifier_move_to_index({'object': target}, modifier="Data Transfer", index=0)
    bpy.ops.object.datalayout_transfer({'object': target}, modifier="Data Transfer")
    bpy.ops.object.modifier_apply({'object': target}, modifier="Data Transfer")
    
#   If armature was disabled - enable it 

    if 'Armature' in target.modifiers:
        target.modifiers['Armature'].show_viewport = True
    if 'Armature' in source.modifiers:
        source.modifiers['Armature'].show_viewport = True
        
#   Hide proxy object
    source.hide_set(True)
    

# Assign rigify type to multiple bones

def set_rigify_type(type_to_assign):
    selected = bpy.context.selected_pose_bones
    for bone in selected:
        bone.rigify_type = f"basic.{type_to_assign}"

# Get indexes of currently active rig layers        
        
def get_active_rig_layers():
    armature = this.scene.objects.get('demo_generated')
    active_layers = []
    for i in range(len(armature.data.layers)):
        if armature.data.layers[i]:
            active_layers.append(str(i))
    return (separator.join(active_layers))


# Write indexes to dict

def save_active_rig_layers(name, storage):
    storage[name] = get_active_rig_layers()
    
    
# Load rig layer from dict storage
    
def load_rig_layer(key):
    layer_str = this.scene.collection["rig_layers_data"][key]
    to_activate = [int(x) for x in layer_str.split(separator)]
    for i in range(len(this.object.data.layers)):
        this.object.data.layers[i] = i in to_activate
        
        
# Remove rig layer from dict storage        
        
def remove_rig_layer(key):
    if key != 'ALL':
        this.scene.collection["rig_layers_data"].pop(key, None)
        
# Callback to dynamically add items to dropdown list        
        
def add_items_from_collection_callback(self, context):
    items = []
    scene = context.scene
    for naming in this.scene.collection["rig_layers_data"].keys():
        items.append((naming, naming, ""))
    return items

# Rig Helper Settings   

class AddonSettings(PropertyGroup):
    
    proxy_switch : EnumProperty(
        items=[
            ('PROXY', 'Proxy', 'Set switch mode to proxy', '', 0),
            ('ORIG', 'Original', 'Set switch mode to original', '', 1)
        ],
        default='ORIG'
    )
    proxy_suffix : StringProperty(
        name="Proxy Suffix",
        description="Proxy string property",
        default = 'Proxy'
    )
    orig_suffix : StringProperty(
        name="Original Suffix",
        description="Original string property",
        default = 'Original'
    )  
    hook_switch : BoolProperty(
        description="A bool property",
        default = True
        )
    rigify_assign_type : StringProperty(
        name="Type",
        description="Rigify type property",
        default = ''
    )
    layer_preset_name : StringProperty(
        name="Preset Name",
        description="Preset name property",
        default = ''
    )
    rig_layers_presets : EnumProperty(
        name="Presets",
        description="Rig Layer Presets",
        items=add_items_from_collection_callback,
    )
    weight_transfer_method : EnumProperty(
        name="Method",
        description="Enum property",
        default = 'ALL',
        items = (
        ('ALL', 'All', "All layers enabled")
        )
    )
    weight_transfer_from : StringProperty(
        name="From",
        description="Object name property",
        default = ''
    )
    weight_transfer_to : StringProperty(
        name="To",
        description="Object name property",
        default = ''
    )
    weight_transfer_method : EnumProperty(
        name="Method",
        description="Enum property",
        default = 'POLYINTERP_NEAREST',
        items = (
        ('TOPOLOGY', 'Topology', "Copy from identical topology meshes"), 
        ('NEAREST', 'Nearest Vertex', "Copy from closest vertex"),
        ('EDGE_NEAREST', 'Nearest Edge Vertex', "Copy from closest vertex of closest edge"),
        ('EDGEINTERP_NEAREST', 'Nearest Edge Interpolated', "Copy from interpolated values of vertices from closest point on closest edge"),
        ('POLY_NEAREST', 'Nearest Face Vertex', "Copy from closest vertex of closest face"),
        ('POLYINTERP_NEAREST', 'Nearest Face Interpolated', "Copy from interpolated values of vertices from closest point on closest face"),
        ('POLYINTERP_VNORPROJ', 'Projected Face Interpolated', "Copy from interpolated values of vertices from point on closest face hit by normal-projection")
        )
    )        
    
    
    
# PROXY SWITCH PANEL

# Proxy switcher button logic 

class ProxySwitcherButtonOperator(bpy.types.Operator):
    """Swaps proxy and original meshes"""
    bl_idname = "object.switch_proxy"
    bl_label = "Proxy switcher"

    def execute(self, context):        
        settings = context.scene.rig_helper_settings
        switch_proxies(mode=settings.proxy_switch, proxy_suffix=settings.proxy_suffix, original_suffix=settings.orig_suffix)
        return {'FINISHED'}    

# Proxy panel layout

class ProxySwitcherPanel(bpy.types.Panel):
    # Panel Naming    
    bl_label = "Proxy Switcher"
    
    bl_idname = "OBJECT_PT_proxy_switcher"
    bl_space_type = 'VIEW_3D'
    # UI to add to sidebar 
    bl_region_type = 'UI'
    bl_category = "Rigging Helper"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.rig_helper_settings
        layout.prop(settings, "proxy_suffix")
        layout.prop(settings, "orig_suffix")
        
#        label = "Original" if settings.proxy_switch else "Proxy"
#        layout.prop(wm, 'my_operator_toggle', text=label, toggle=True)
        layout.prop(settings, "proxy_switch", expand=True)

        obj = context.object

        row = layout.row()
        row.operator(ProxySwitcherButtonOperator.bl_idname, text="Switch", icon='UV_SYNC_SELECT')


# HOOK SWITCH PANEL

class HookTransferButtonOperator(bpy.types.Operator):
    """Swaps hooks between meta and generated rig"""
    bl_idname = "object.hook_transfer"
    bl_label = "Hook Transfer"

    def execute(self, context):        
        settings = context.scene.rig_helper_settings
        transfer_hooks(settings.hook_switch)
        return {'FINISHED'}
    
class HookTransferPanel(bpy.types.Panel):
    # Panel Naming    
    bl_label = "Curve Hook Transfer"
    
    bl_idname = "OBJECT_PT_hook_transfer"
    bl_space_type = 'VIEW_3D'
    # UI to add to sidebar 
    bl_region_type = 'UI'
    bl_category = "Rigging Helper"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.rig_helper_settings
        layout.prop(settings, "hook_switch", text='Retarget to Generated')

        obj = context.object

        row = layout.row()
        row.operator(HookTransferButtonOperator.bl_idname, text="Transfer", icon='UV_SYNC_SELECT')


# TRANSFER WEIGHTS PANEL

class TransferWeightsButtonOperator(bpy.types.Operator):
    """Transfer weights from one mesh to another"""
    bl_idname = "object.transfer_weights"
    bl_label = "Transfer Weights"

    def execute(self, context):        
        settings = context.scene.rig_helper_settings
        transfer_weights(
        obj_from=settings.weight_transfer_from,
        obj_to=settings.weight_transfer_to,
        method=settings.weight_transfer_method
        )
        return {'FINISHED'}    

class TransferWeightsPanel(bpy.types.Panel):
    # Panel Naming    
    bl_label = "Transfer Weights"
    
    bl_idname = "OBJECT_PT_transfer_weights"
    bl_space_type = 'VIEW_3D'
    # UI to add to sidebar 
    bl_region_type = 'UI'
    bl_category = "Rigging Helper"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.rig_helper_settings
        layout.prop_search(settings, 'weight_transfer_from', scene, "objects")
        layout.prop_search(settings, 'weight_transfer_to', scene, "objects")
        layout.prop(settings, "weight_transfer_method")
        obj = context.object

        row = layout.row()
        row.operator(TransferWeightsButtonOperator.bl_idname, text="Transfer", icon='UV_SYNC_SELECT')

# ASSIGN RIGIFY TYPE PANEL

class RigifyAssignButtonOperator(bpy.types.Operator):
    """Assign rigify type to multiple bones"""
    bl_idname = "object.rigify_assign"
    bl_label = "Rigify Assign"

    def execute(self, context):        
        settings = context.scene.rig_helper_settings
        set_rigify_type(settings.rigify_assign_type)
        return {'FINISHED'}
    
class RigifyAssignPanel(bpy.types.Panel):
    # Panel Naming    
    bl_label = "Rigify Multiple Assign"
    
    bl_idname = "OBJECT_PT_rigify_assign"
    bl_space_type = 'VIEW_3D'
    # UI to add to sidebar 
    bl_region_type = 'UI'
    bl_context = "posemode"
    bl_category = "Rigging Helper"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.rig_helper_settings
        layout.prop(settings, "rigify_assign_type")

        obj = context.object

        row = layout.row()
        row.operator(RigifyAssignButtonOperator.bl_idname, text="Apply to selected", icon='CHECKMARK')


# SAVE RIG LAYER PRESET PANEL

class LayerPresetSave(bpy.types.Operator):
    """Save rig layers preset"""
    bl_idname = "object.rig_layers_save_preset"
    bl_label = "Save Preset"

    def execute(self, context):        
        settings = context.scene.rig_helper_settings
        rig_presets = this.scene.collection["rig_layers_data"]
        save_active_rig_layers(settings.layer_preset_name, rig_presets)
        
#        set_rigify_type(settings.rigify_assign_type)
        return {'FINISHED'}
    
class LayerPresetLoad(bpy.types.Operator):
    """Load rig layers preset"""
    bl_idname = "object.rig_layers_load_preset"
    bl_label = "Load Preset"

    def execute(self, context):        
        settings = context.scene.rig_helper_settings
        load_rig_layer(settings.rig_layers_presets)
#        set_rigify_type(settings.rigify_assign_type)
        return {'FINISHED'}
    
class LayerPresetRemove(bpy.types.Operator):
    """Remove rig layers preset"""
    bl_idname = "object.rig_layers_remove_preset"
    bl_label = "Remove Preset"

    def execute(self, context):        
        settings = context.scene.rig_helper_settings
        remove_rig_layer(settings.rig_layers_presets)
#        set_rigify_type(settings.rigify_assign_type)
        return {'FINISHED'}
    
class LayerPresetPanel(bpy.types.Panel):
    # Panel Naming    
    bl_label = "Rig Layers Presets"
    
    bl_idname = "OBJECT_PT_rig_layers_presets"
    bl_space_type = 'VIEW_3D'
    # UI to add to sidebar 
    bl_region_type = 'UI'
    bl_category = "Rigging Helper"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.rig_helper_settings
        layout.prop(settings, "layer_preset_name")
        layout.operator(LayerPresetSave.bl_idname, text="Save Preset", icon='PLUS')
        layout.prop(settings, 'rig_layers_presets', expand=True)
#        layout.prop(settings, "rigify_assign_type")

        obj = context.object

        row = layout.row()
        row.operator(LayerPresetLoad.bl_idname, text="Load", icon='EMPTY_SINGLE_ARROW')
        row.operator(LayerPresetRemove.bl_idname, text="Remove", icon='PANEL_CLOSE')
#                        row.operator(LayerPresetSave.bl_idname, text="Save Preset", icon='PLUS')

# REG / UNREG

from bpy.utils import register_class, unregister_class

_classes = [ProxySwitcherButtonOperator, ProxySwitcherPanel, AddonSettings,
HookTransferButtonOperator, HookTransferPanel, TransferWeightsButtonOperator,
TransferWeightsPanel, RigifyAssignPanel, RigifyAssignButtonOperator,
LayerPresetSave, LayerPresetLoad, LayerPresetRemove, LayerPresetPanel]

def register():
    for cls in _classes:
        register_class(cls)
    bpy.types.Scene.rig_helper_settings = PointerProperty(type=AddonSettings)
    this.scene.collection["rig_layers_data"] = {'ALL':'0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31'} 

    
def unregister():
    for cls in _classes:
        unregister_class(cls)
    del bpy.types.Scene.rig_helper_settings
    del bpy.types.Scene.rig_presets
        
if __name__ == "__main__":
    register()
    

    




    
