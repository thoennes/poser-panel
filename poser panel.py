bl_info = {
	'name': 'Poser Panel',
	'description': 'Tools for working with Poser meshes',
	'category': 'Mesh',
	'blender': (2, 80, 0),
	'author': 'unreal',
	'version': (1, 1, 0)
}

import mathutils
import bpy
from bpy.types import Scene, Object, Panel, Operator
from bpy.props import IntProperty, BoolProperty, PointerProperty, StringProperty
from bpy.utils import register_class, unregister_class
import pprint


logfile = open('/Users/thoennes/Desktop/poser-panel-log.txt', 'w')


PRECISION = 100000

def vectorKey(self, vector, precision = PRECISION):
	'''Return vector * PRECISION as INT tuple'''
	return tuple([int(value) for value in vector * precision])

def copyMesh(self, context, mesh):
	'''Copy mesh'''

	print('> copyMesh()')

	new = mesh.copy()
	new.data = mesh.data.copy()
	context.collection.objects.link(new)
	print('    -> Mesh copied.')

	return new

def mapMeshes(self, mesh1, mesh2, precision = PRECISION):
	'''Return maps of (x,y,z) keyed indexes for mesh1 and mesh2}'''

	print('> mapMeshes()')

	map1 = {}
	map2 = {}
	map3 = {}

	i = 0
	for vertex in mesh1.data.vertices:
		xyz = vectorKey(self, vertex.co, precision)
		map1.setdefault(xyz, []).append(i)
		map3.setdefault(xyz, {'map1':[], 'map2':[]})['map1'].append(i)
		i += 1

	i = 0
	for vertex in mesh2.data.vertices:
		xyz = vectorKey(self, vertex.co, precision)
		map2.setdefault(xyz, []).append(i)
		map3.setdefault(xyz, {'map1':[], 'map2':[]})['map2'].append(i)
		i += 1

	# pp = pprint.PrettyPrinter()
	# pp.pprint(map3)

	if not (map1.keys() == map2.keys()):
		print('   -> Meshes are not the exact same shape; (mesh1: %s mesh2: %s); precision = %s' % (len(map1), len(map2), precision), file=logfile)
		return

	print('    -> Map is valid.')
	return map1, map2

def compareMeshes(self, mesh1, mesh2, precision = PRECISION):
	'''Return result of check OR None if no issues'''

	print('COMPARE MESHES', file=logfile)
	# check1: (quickest) same number of verts
	if (len(mesh1.data.vertices) != len(mesh2.data.vertices)):
		return 'vert count not equal; (mesh1: %s mesh2: %s)' % (len(mesh1.data.vertices), len(mesh2.data.vertices))

	# check2: (second quickest) same vert groups
	mesh1_vgroups = { vgroup.index: vgroup.name for vgroup in mesh1.vertex_groups }
	mesh2_vgroups = { vgroup.index: vgroup.name for vgroup in mesh2.vertex_groups }
	if (mesh1_vgroups != mesh2_vgroups):
		return 'vert groups not the same; (mesh1: %s mesh2: %s)' % (len(mesh1_vgroups), len(mesh2_vgroups))

	# check 3: (slowest) vert groups composed of same verts (ordered lists)
	mesh1_verts = { name: [] for name in mesh1_vgroups.values() }
	for vertex in mesh1.data.vertices:
		for vgroup in vertex.groups:
			mesh1_verts[mesh1_vgroups[vgroup.group]].append(vertex.index)

	mesh2_verts = {name: [] for name in mesh2_vgroups.values()}
	for vertex in mesh2.data.vertices:
		for vgroup in vertex.groups:
			mesh2_verts[mesh2_vgroups[vgroup.group]].append(vertex.index)

	if (mesh1_verts != mesh2_verts):
		return 'vert groups not equal'

	return

def poserCheckMeshes(self, context, mesh):
	PRECISION = 10**context.scene.Precision

	print('> poserCheckMeshes(%s)' % (mesh), self, context)

	if mesh == 'base' or mesh == 'zero':
		self.poser_same_mesh_shape = False
		mesh1 = self.poser_original_mesh
		mesh2 = self.poser_zero_mesh

		if (mesh1 is None or mesh2):
			print ('    -> Mapping base <-> zero not possible.')
		else:
			print ('    -> Mapping base <-> zero ...')
			maps = None
			maps = mapMeshes(self, mesh1 = mesh1, mesh2 = mesh2, precision = PRECISION)
			if maps is None:
				return
			self.poser_same_mesh_shape = True
			print ('    -> Mapped base <-> zero.')

	if mesh == 'zero' or mesh == 'morph':
		self.poser_same_mesh_struct = False
		mesh1 = self.poser_zero_mesh
		mesh2 = self.poser_morphed_mesh

		if (mesh1 is None or mesh2 is None):
			print ('    -> Checking structure zero <-> morph not possible.')
		else:
			check = None
			print ('    -> Checking structure zero <-> morph ...')
			check = compareMeshes(self, mesh1 = mesh1, mesh2 = mesh2, precision = PRECISION)
			if (check is not None):
				print (check)
				return
			self.poser_same_mesh_struct = True
			print ('    -> Checked structure zero <-> morph.')

	if mesh == 'base' or mesh == 'morph' or mesh == 'unimesh':
		self.poser_same_mesh_shape_and_struct = False

		same_mesh_shape = False
		same_mesh_struct = False

		mesh1 = self.poser_morphed_mesh
		mesh2 = self.poser_uni_mesh

		if (mesh1 is None or mesh2 is None):
			print ('    -> Mapping morphed <-> unimesh not possible.')
		else:
			print ('    -> Mapping morphed <-> unimesh ...')
			maps = None
			maps = mapMeshes(self, mesh1 = mesh1, mesh2 = mesh2, precision = PRECISION)
			if maps is None:
				return
			same_mesh_shape = True
			print ('    -> Mapped morphed <-> unimesh.')

		mesh1 = self.poser_original_mesh
		mesh2 = self.poser_uni_mesh

		if (mesh1 is None or mesh2 is None):
			print ('    -> Checking structure base <-> unimesh not possible.')
		else:
			check = None
			print ('    -> Checking structure base <-> unimesh...')
			check = compareMeshes(self, mesh1 = mesh1, mesh2 = mesh2, precision = PRECISION)
			if (check is not None):
				return
			same_mesh_struct = True
			print ('    -> Checked structure base <-> unimesh.')

		if (same_mesh_shape and same_mesh_struct):
			self.poser_same_mesh_shape_and_struct = True

class PoserWriteUnimesh(Operator):
	bl_idname = 'poser.write_unimesh'
	bl_label = 'Write Morphed Original'
	bl_description = 'Writes Morphed Mesh shape to Morphed Original Mesh'

	@classmethod
	def poll(cls, context):
		if (context.scene.poser_same_mesh_shape and context.scene.poser_same_mesh_struct):
			return True

	def __init__(self):
		PRECISION = 100000

	def execute(self, context):

		print('PoserWriteUnimesh.execute()')

		basemap = None
		zeromap = None
		maps = None
		PRECISION = 10**context.scene.Precision
		maps = mapMeshes(
			self,
			mesh1 = context.scene.poser_original_mesh,
			mesh2 = context.scene.poser_zero_mesh,
			precision = PRECISION
		)
		if maps is None:
			self.report(
				type = {'ERROR'},
				message = 'Mapping failed'
			)
			return {'CANCELLED'}

		basemap, zeromap = maps

		if context.scene.poser_uni_mesh is None:
			context.scene.poser_uni_mesh = copyMesh(self, context, context.scene.poser_original_mesh)
		if context.scene.poser_uni_mesh is None:
			self.report(
				type = {'ERROR'},
				message = 'Missing unimesh target'
			)
		else:
			print('    -> Writing unimesh...')
			# do this as a shapekey
			# keyName = None
			# if context.scene.poser_morph_as_shapekey:
			# 	if context.scene.poser_uni_mesh.data.shape_keys:
			# 		keyName = getattr(context.scene.poser_uni_mesh.active_shape_key, 'name', None)
			# 		if keyName == 'Basis':
			# 			sk = context.scene.poser_uni_mesh.shape_key_add()
			# 			keyName = getattr(sk, 'name', None)
			# 	if not keyName:
			# 		sk_basis = context.scene.poser_uni_mesh.shape_key_add(name = 'Basis')
			# 		sk = context.scene.poser_uni_mesh.shape_key_add()
			# 		keyName = getattr(sk, 'name', None)
			for xyz, zero_vertices in zeromap.items():
				for tv in zero_vertices:
					for bv in basemap[xyz]:
						# if keyName:
						# 	context.scene.poser_uni_mesh.data.shape_keys.key_blocks[keyName].data[bv].co = context.scene.poser_morphed_mesh.data.vertices[tv].co
						# else:
						context.scene.poser_uni_mesh.data.vertices[bv].co = context.scene.poser_morphed_mesh.data.vertices[tv].co
			print('    -> Unimesh written.')
			poserCheckMeshes(context.scene, context, 'unimesh')

		return {'FINISHED'}

class PoserCastMesh(Operator):
	bl_idname = 'poser.cast_mesh'
	bl_label = 'Write Morphed'
	bl_description = 'Writes Morphed Original Mesh shape to Morphed Mesh'

	@classmethod
	def poll(cls, context):
		if (context.scene.poser_same_mesh_shape_and_struct):
			return True

	def __init__(self):
		PRECISION = 100000

	def execute(self, context):

		print('PoserCastMesh.execute()')

		PRECISION = 10**context.scene.Precision

		basemap = None
		zeromap = None
		maps = None

		maps = mapMeshes(
			self,
			mesh1 = context.scene.poser_original_mesh,
			mesh2 = context.scene.poser_zero_mesh,
			precision = PRECISION
		)

		if maps is None:
			self.report(
				type = {'ERROR'},
				message = 'Mapping failed'
			)
			return {'CANCELLED'}

		basemap, zeromap = maps

		if context.scene.poser_morphed_mesh is None:
			context.scene.poser_morphed_mesh = copyMesh(self, context, context.scene.poser_zero_mesh)

		if context.scene.poser_morphed_mesh is None:
			self.report(
				type = {'ERROR'},
				message = 'Missing unwelded target'
			)
		else:
			for xyz, base_vertices in basemap.items():
				for bv in base_vertices:
					for tv in zeromap[xyz]:
						context.scene.poser_morphed_mesh.data.vertices[tv].co = context.scene.poser_uni_mesh.data.vertices[bv].co

		print('    -> Unimesh cast.')

		return {'FINISHED'}

class PoserCopyVectors(Operator):
	bl_idname = 'poser.copy_vectors'
	bl_label = 'Copy Selected'
	bl_description = 'Writes selected vert vectors verts to Morphed Original Mesh'

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return
		selectedVerts = [v for v in bpy.context.active_object.data.vertices if v.select]
		if (context.scene.poser_uni_mesh is not None and len(selectedVerts) > 0):
			return True

	def execute(self, context):

		print('PoserCopyVectors.execute()')

		mode = bpy.context.active_object.mode
		# we need to switch from Edit mode to Object mode so the selection gets updated
		bpy.ops.object.mode_set(mode = 'OBJECT')
		selectedVerts = [v for v in bpy.context.active_object.data.vertices if v.select]

		target = context.scene.poser_uni_mesh

		for v in selectedVerts:
			target.data.vertices[v.index].co = v.co

		# back to whatever mode we were in
		bpy.ops.object.mode_set(mode = mode)

		print('    -> Vectors copied.')

		return {'FINISHED'}

class PoserTweakMesh(Operator):
	bl_idname = 'poser.tweak_mesh'
	bl_label = 'Nudge Zero'
	bl_description = 'Nudges verts in the Zero Mesh into the same positions as the Original Mesh'

	@classmethod
	def poll(cls, context):
		if context.scene.poser_original_mesh is not None and context.scene.poser_zero_mesh is not None and not context.scene.poser_same_mesh_shape:
			return True

	def execute(self, context):
		base = context.scene.poser_original_mesh
		zero = context.scene.poser_zero_mesh

		j = 0
		for tv in zero.data.vertices:
			closest_bv = mathutils.Vector((100000, 100000, 100000))
			closest_bv_i = 0
			i = 0
			for bv in base.data.vertices:
				d = tv.co - bv.co
				if d < closest_bv:
					closest_bv = d
					closest_bv_i = i
				i += 1
			zero.data.vertices[j].co = base.data.vertices[closest_bv_i].co
			j += 1


		return {'FINISHED'}

class PoserPanel(Panel):
	'''Poser Mesh Tools panel'''
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Poser Unimesh"
	bl_idname = "VIEW3D_PT_poser_meshes"
	bl_label = "Poser Mesh Tools"

	def draw(self, context):
		scene = context.scene
		layout = self.layout

		layout.use_property_split = True
		layout.use_property_decorate = False

		row = layout.row()
		row.label(text='Meshes')

		box = layout.box()

		col = box.column()

		col.prop_search(scene, 'poser_original_mesh', scene, 'objects', icon = 'MESH_DATA')

		split = col.split(factor = .40)
		col1 = split.column()
		col1.label(text = '')

		col2 = split.column()
		if scene.poser_same_mesh_shape:
			col2.label(icon = 'LINKED')
		else:
			col2.label(icon = 'UNLINKED')

		col.prop_search(scene, 'poser_zero_mesh', scene, 'objects', icon = 'MESH_DATA')

		split = col.split(factor = .40)
		col1 = split.column()
		col1.label(text = '')
		col2 = split.column()
		if scene.poser_same_mesh_struct:
			col2.label(icon = 'LINKED')
		else:
			col2.label(icon = 'UNLINKED')

		col.prop_search(scene, 'poser_morphed_mesh', scene, 'objects', icon = 'MESH_DATA')

		split = col.split(factor = .40)
		col1 = split.column()
		col1.label(text = '')
		col2 = split.column()
		if scene.poser_same_mesh_shape_and_struct:
			col2.label(icon = 'LINKED')
		else:
			col2.label(icon = 'UNLINKED')

		col.prop_search(scene, 'poser_uni_mesh', scene, 'objects', icon = 'MESH_DATA')

		row = layout.row()
		row.label(text='Operations')

		box = layout.box()

		box.prop(scene, 'Precision')

		# grid = box.column()
		# grid.prop(scene, 'poser_morph_as_shapekey')

		split = box.split(factor = .40)

		grid = split.column()
		grid.label(text = '')

		grid = split.column()
		grid.operator('poser.write_unimesh')
		grid.operator('poser.cast_mesh')
		grid.operator('poser.copy_vectors')
		grid.operator('poser.tweak_mesh')

CLASSES = [
	PoserWriteUnimesh,
	PoserCastMesh,
	PoserCopyVectors,
	PoserTweakMesh,
	PoserPanel
]

def register():
	Scene.Precision = IntProperty(
		name = 'Precision',
		description = 'Number of decimal places of precision',
		default = 6,
		min = 1,
		max = 6
	)
	Scene.poser_original_mesh = PointerProperty(
		type = Object,
		name = 'Original Mesh',
		description = 'From Poser Geometries folder',
		update = lambda self, context: poserCheckMeshes(self, context, mesh = 'base')
	)
	Scene.poser_zero_mesh = PointerProperty(
		type = Object,
		name = 'Zero Mesh',
		description = 'From Poser OBJ export: no IK, zero all, welded or unwelded, as Morph Target, include body part names; welding must match Morphed mesh',
		update = lambda self, context: poserCheckMeshes(self, context, mesh = 'zero')
	)
	Scene.poser_morphed_mesh = PointerProperty(
		type = Object,
		name = 'Morphed Mesh',
		description = 'From Poser OBJ export: no IK, *morphed*, zero rotations and transformations, welded or unwelded, *not* as Morph Target, include body part names; welding must match Zero mesh',
		update = lambda self, context: poserCheckMeshes(self, context, mesh = 'morph')
	)
	Scene.poser_uni_mesh = PointerProperty(
		type = Object,
		name = 'Morphed Original Mesh',
		description = "Must match Original OBJ structure (vert count, order, vert groups) but may have any shape (vert xyz's don't have to match => they may be set from Morphed Mesh",
		update = lambda self, context: poserCheckMeshes(self, context, mesh = 'unimesh')
	)
	# Scene.poser_morph_as_shapekey = BoolProperty(
	# 	name = 'As Shape Key',
	# 	description = 'Create or add the Morphed Mesh as a shapekey rather than as the base mesh shape'
	# )
	Scene.poser_same_mesh_shape = BoolProperty(
		name = 'Same Mesh Shape',
		description = 'Two meshes have the same shape'
	)
	Scene.poser_same_mesh_struct = BoolProperty(
		name = 'Same Mesh Struct',
		description = 'Two meshes have the same vertex group structures'
	)
	Scene.poser_same_mesh_shape_and_struct = BoolProperty(
		name = 'Same Mesh Shape and Struct',
		description = 'Two meshes have the same mesh shape AND vertex group structures'
	)
	for CLASS in CLASSES:
		register_class(CLASS)

def unregister():
	for CLASS in CLASSES:
		unregister_class(CLASS)

if __name__ == '__main__':
    register()
