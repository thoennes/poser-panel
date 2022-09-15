# poser-panel
A Blender Add-on to help working with Poser exported OBJ files in Blender

## Summary
Using 3 specific OBJ files, shapes a 4th object that has the same internal structure as the first object but is shaped like the 3rd object.

## Background Problem
During Figure creation, Poser splits the source OBJ unimesh into sub-meshes which are used internally.  Poser can also use OBJ files with the same structure as the original source OBJ.  IE: the same vert count, vert order, faces, and polygons.

However, Poser loses the original OBJ structure during Figure creation.  The result of this is that Poser cannot export an OBJ from the Figure that it can use directly as a geometry source for a Figure "Full Body Morph".   In short, Poser exports vertices in a different order than the original OBJ.

> Caveat: Poser can export the mesh as an OBJ in the split form it uses internally.  The vertex XYZ's may be edited in the OBJ, without changing the OBJ structure and this "split mesh differently ordered" OBJ can be used as a as a geometry source.  This is because the mesh is already split, which means it's already in the order Poser uses.  The reason a geometry OBJ file has to be structured the same as the source is so that when Poser splits the mesh, it splits it the same way as the original the source mesh.

> This might be usable in some cases.  However, Blender scultping does not work well on split meshes.  Generally you want a unimesh for scultping.  If you just wanted to make a figure mesh from scratch, you could import the source OBJ then export that and use it directly in Blender.

But suppose you want a Figure that's already been morphed in Poser?  And you want to modify that morph in Blender?  You can't do it because the welded (unimesh) morphed exported OBJ from Poser can't be used as a morph in Poser.

# Description of Solution
This Add-on uses some of the characteristics of Poser export, OBJs, and Blender import to bridge this gap.

1. Poser exports a zero'd welded mesh with the vertices all in the same exact position as the source OBJ.  Just in a different order.  Poly-groups, UVs, and mats are maintained.  Regardless of the xyz of verts, Poser always exports as OBJ the same figure in the same order.
3. Blender can import an OBJ maintining the source order, UVs, and mats. 

Consider, with the XYZ's the same for verts in 2 files, we can use them as a lookup key.  That is for file one, v1(x1,y1,z1) while for file 2 it might be v100(x1,y1,z1).  This means that v1 in file 1 is v100 in file 2.  A map!
Let's say we have file 3, which has a different shape but is structured the same as file 2, but with different x,y,z for the vert (a morph).

If we want to change the original file, we set all the verts in fiole 1 to values in file 3, looking up which vert in 1 shoulld be changed for each vert in 3.  EG:see that v100 in file 3 is v1 in file 1.  So set v1(x,y,z) = to v100(x,y,z)

