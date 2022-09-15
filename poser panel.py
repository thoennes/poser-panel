bl_info = {
	'name': 'Poser Panel',
	'description': 'Tools for working with Poser meshes',
	'category': 'Mesh',
	'blender': (2, 80, 0),
	'author': 'unreal',
	'version': (1, 0, 2)
}

import bpy
from bpy.types import Scene, Object, Panel, Operator
from bpy.props import IntProperty, BoolProperty, PointerProperty
from bpy.utils import register_class, unregister_class

PRECISION = 100000

class View3DPanel:
	'''Poser Unimesh Tools container panel'''
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Poser Unimesh"

class MapPanel(View3DPanel, Panel):
	'''Poser Unimesh Tools mapping setup subpanel; mapping between unimesh and unwelded zero mesh'''
	bl_idname = "VIEW3D_PT_poser_unimesh_mapping"
	bl_label = "Mapping"

	def draw(self, context):
		scene = context.scene
		layout = self.layout

		layout.use_property_split = True
		layout.use_property_decorate = False

		row = layout.row()
		row.prop(scene, 'Precision')

		column = layout.column()
		column.prop_search(scene, 'poser_original_mesh', scene, 'objects', icon='MESH_DATA')
		column.prop_search(scene, 'poser_zero_mesh', scene, 'objects', icon='MESH_DATA')

class OperatorPanel(View3DPanel, Panel):
	'''Poser Unimesh Tools operations subpanel; copy unmiesh to unwelded or unwelded to unimesh'''
	bl_idname = "VIEW3D_PT_poser_unimesh_operators"
	bl_label = "Operations"

	def draw(self, context):
		scene = context.scene
		layout = self.layout

		layout.use_property_split = True
		layout.use_property_decorate = False

		col = layout.column()
		col.prop_search(scene, 'poser_morphed_mesh', scene, 'objects', icon='MESH_DATA')

		col.separator()

		split = col.split(factor=.40)
		grid = split.column()
		grid.label(text='')
		grid = split.column()
		grid.operator('poser.cast_mesh', icon='SORT_DESC')

		split = col.split(factor=.40)
		grid = split.column()
		grid.label(text='')
		grid = split.column()
		grid.operator('poser.write_unimesh', icon='SORT_ASC')

		col.separator()
		col.prop(scene, 'poser_morph_as_shapekey')

		col.separator()

		col.prop_search(scene, 'poser_uni_mesh', scene, 'objects', icon='MESH_DATA')

		col.separator()

		split = col.split(factor=.40)
		grid = split.column()
		grid.label(text='')
		grid = split.column()
		grid.operator('poser.copy_vectors')

class PoserCopyVectors(Operator):
	bl_idname = 'poser.copy_vectors'
	bl_label = 'Copy Vectors'
	bl_description = 'Copies vectors of selected verts to target mesh'

	def execute(self, context):
		mode = bpy.context.active_object.mode
		# we need to switch from Edit mode to Object mode so the selection gets updated
		bpy.ops.object.mode_set(mode='OBJECT')
		selectedVerts = [v for v in bpy.context.active_object.data.vertices if v.select]


		target = context.scene.poser_uni_mesh

		for v in selectedVerts:
			target.data.vertices[v.index].co = v.co

		# back to whatever mode we were in
		bpy.ops.object.mode_set(mode=mode)
		return {'FINISHED'}

def vectorKey(self, vector):
	'''Return vector * PRECISION as INT tuple'''
	return tuple([int(value) for value in vector * PRECISION])

def copyMesh(self, context, mesh):
	'''Copy mesh'''
	new = mesh.copy()
	new.data = mesh.data.copy()
	context.collection.objects.link(new)
	return new

def mapMeshes(self, base, target):
	'''Return (x,y,z) keyed basemap and targetmap}'''
	objmap = {}
	basemap = {}
	targetmap = {}

	i = 0
	if base is None:
		self.report(
			type={'ERROR'},
			message='Missing base mesh'
		)
		return
	if target is None:
		self.report(
			type={'ERROR'},
			message='Missing target mesh'
		)
		return
	for vertex in base.data.vertices:
		xyz = vectorKey(self, vertex.co)
		objmap.setdefault(xyz, {'base':[], 'target':[]})['base'].append(i)
		basemap.setdefault(xyz, []).append(i)
		i += 1

	i = 0
	for vertex in target.data.vertices:
		xyz = vectorKey(self, vertex.co)
		objmap.setdefault(xyz, {'base':[], 'target':[]})['target'].append(i)
		targetmap.setdefault(xyz, []).append(i)
		i += 1

	# +++ DEBUG
	# print('basemap', len(basemap))
	# print('targetmap', len(targetmap))
	# print('objmap', len(objmap))

	# for xyz, target_vertices in targetmap.items():
	# 	print(xyz, targetmap[xyz], basemap[xyz])
	# --- DEBUG

	if not (len(objmap) == len(basemap) == len(targetmap)):
		self.report(
			type={'ERROR'},
			# message='%s %s %s' % (len(objmap), len(basemap), len(targetmap))
			message='Target mesh does not exactly vertex overlap base mesh; map lengths (obj=%s base=%s target=%s); precision=%s' % (
				len(objmap),
				len(basemap),
				len(targetmap),
				PRECISION
			)
		)
		return

	return basemap, targetmap

class PoserWriteUnimesh(Operator):
	bl_idname = 'poser.write_unimesh'
	bl_label = 'Make Unimesh'
	bl_description = 'Copies the unwelded morph shape to the unimesh morph'

	@classmethod
	def poll(cls, context):
		if None not in {context.scene.poser_original_mesh, context.scene.poser_zero_mesh, context.scene.poser_morphed_mesh}:
			return True

	def __init__(self):
		PRECISION = 100000

	def execute(self, context):
		basemap = None
		targetmap = None
		maps = None

		PRECISION = 10**context.scene.Precision

		maps = mapMeshes(self, base=context.scene.poser_original_mesh, target=context.scene.poser_zero_mesh)
		if maps is None:
			self.report(
				type={'ERROR'},
				message='Mapping failed'
			)
			return {'CANCELLED'}
		basemap, targetmap = maps
		if context.scene.poser_uni_mesh is None:
			context.scene.poser_uni_mesh = copyMesh(self, context, context.scene.poser_original_mesh)
		if context.scene.poser_uni_mesh is None:
			self.report(
				type={'ERROR'},
				message='Missing unimesh target'
			)
		else:
			# do this as a shapekey
			keyName = None
			if context.scene.poser_morph_as_shapekey:
				if context.scene.poser_uni_mesh.data.shape_keys:
					keyName = getattr(context.scene.poser_uni_mesh.active_shape_key, 'name', None)
					if keyName == 'Basis':
						sk = context.scene.poser_uni_mesh.shape_key_add()
						keyName = getattr(sk, 'name', None)
				if not keyName:
					sk_basis = context.scene.poser_uni_mesh.shape_key_add(name = 'Basis')
					sk = context.scene.poser_uni_mesh.shape_key_add()
					keyName = getattr(sk, 'name', None)

			for xyz, target_vertices in targetmap.items():
				for tv in target_vertices:
					for bv in basemap[xyz]:
						if keyName:
							context.scene.poser_uni_mesh.data.shape_keys.key_blocks[keyName].data[bv].co = context.scene.poser_morphed_mesh.data.vertices[tv].co
						else:
							context.scene.poser_uni_mesh.data.vertices[bv].co = context.scene.poser_morphed_mesh.data.vertices[tv].co
		return {'FINISHED'}

class PoserCastMesh(Operator):
	bl_idname = 'poser.cast_mesh'
	bl_label = 'Cast Unimesh'
	bl_description = 'Copies the unimesh morph shape to the unwelded morph'

	@classmethod
	def poll(cls, context):
		if None not in {context.scene.poser_original_mesh, context.scene.poser_zero_mesh, context.scene.poser_uni_mesh}:
			return True

	def __init__(self):
		PRECISION = 100000

	def execute(self, context):
		basemap = None
		targetmap = None
		maps = None

		PRECISION = 10**context.scene.Precision

		maps = mapMeshes(self, base=context.scene.poser_original_mesh, target=context.scene.poser_zero_mesh)
		if maps is None:
			self.report(
				type={'ERROR'},
				message='Mapping failed'
			)
			return {'CANCELLED'}
		basemap, targetmap = maps

		if context.scene.poser_morphed_mesh is None:
			context.scene.poser_morphed_mesh = copyMesh(self, context, context.scene.poser_zero_mesh)
		if context.scene.poser_morphed_mesh is None:
			self.report(
				type={'ERROR'},
				message='Missing unwelded target'
			)
		else:
			for xyz, base_vertices in basemap.items():
				for bv in base_vertices:
					for tv in targetmap[xyz]:
						context.scene.poser_morphed_mesh.data.vertices[tv].co = context.scene.poser_uni_mesh.data.vertices[bv].co
		return {'FINISHED'}

def register():
	Scene.Precision = IntProperty(
		name = 'Precision',
		description='Number of decimal places of precision',
		default=6,
		min=1,
		max=6
	)	
	Scene.poser_original_mesh = PointerProperty(
		type = Object,
		name = 'Original Mesh',
		description = 'From Poser Geometries folder'
	)
	Scene.poser_zero_mesh = PointerProperty(
		type = Object,
		name = 'Zero Mesh',
		description = 'From Poser OBJ export: no IK, zero all, welded or unwelded, as Morph Target, include body part names; welding must match Morphed mesh'
	)
	Scene.poser_morphed_mesh = PointerProperty(
		type = Object,
		name = 'Morphed Mesh',
		description = 'From Poser OBJ export: no IK, *morphed*, zero rotations and transformations, welded or unwelded, *not* as Morph Target, include body part names; welding must match Zero mesh'
	)
	Scene.poser_uni_mesh = PointerProperty(
		type = Object,
		name = 'Morphed Original Mesh',
		description = "Must match Original OBJ structure (vert count, order, vert groups) but may have any shape (vert xyz's don't have to match => they will be set from Morphed Mesh through a map to Original Mesh"
	)
	Scene.poser_morph_as_shapekey = BoolProperty(
		name = 'As Shape Key',
		description = "Create or add the Morphed Mesh as a shapekey rather than as the base mesh shape"
	)
	register_class(PoserWriteUnimesh)
	register_class(PoserCastMesh)
	register_class(PoserCopyVectors)
	register_class(MapPanel)
	register_class(OperatorPanel)


def unregister():
	unregister_class(PoserWriteUnimesh)
	unregister_class(PoserCastMesh)
	unregister_class(PoserCopyVectors)
	unregister_class(MapPanel)
	unregister_class(OperatorPanel)
