# poser-panel
A Blender Add-on to help working with Poser exported OBJ files in Blender

## Summary
Using 3 specific OBJ files, shapes a 4th object that has the same internal structure as the first object but is shaped like the 3rd object.

## Background Problem
During Figure creation, Poser splits the source OBJ unimesh into sub-meshes which are used internally.  Poser can also use OBJ files with the same structure as the original source OBJ.  IE: the same vert count, vert order, faces, and polygons.

However, Poser loses the original OBJ structure during Figure creation.  The result of this is that Poser cannot export an OBJ from the Figure that it can use directly as a geometry source for a Figure "Full Body Morph".   In short, Poser exports vertices in a different order than the original OBJ.

> Caveat: Poser can export the mesh as an OBJ in the split form it uses internally.  The vertex XYZ's may be edited in the OBJ, without changing the OBJ structure and this "split mesh differently ordered" OBJ can be used as a as a geometry source.  This is because the mesh is already split, which means it's already in the order Poser uses.  The reason a geometry OBJ file has to be structured the same as the source is so that when Poser splits the mesh, it splits it the same way as the original the source mesh.

> This might be usable in some cases.  However, Blender scultping does not work well on split meshes.  Generally you want a unimesh for scultping.  Otherwise the mesh pulls apart at the seams.  If you just wanted to make a morph starting from the original OBJ mesh, you could import the source OBJ and use it directly in Blender.

But suppose you want a Figure that's already been morphed in Poser?  And you want to modify that morph in Blender?  You can't do it because the morphed exported OBJ from Poser can't be used as a morph in Poser - the vertices are ordered differently than the original OBJ.

# Description of Solution
This Add-on uses some of the characteristics of Poser export, OBJs, and Blender import to counter this problem.

1. Poser exports a zero'd Morph Target mesh with the vertices all in the same exact position as the source OBJ but in a different order.  You don't even need the same number of verts.  Just need it so every vert in the original OBJ exactly overlaps at least one vert in the export OBJ.  In any order.  Poly-groups, UVs, and mats are maintained.  Poser always exports the same Figure as an OBJ the same figure in the same order - just not the original order.
3. Blender can import an OBJ maintaining the source order, UVs, and mats. 

With the XYZ's the same for all verts in two different files, we can make a lookup table of vert to vert indices.  That is in file one, v1(x1,y1,z1) while in file 2 it might be v100(x1,y1,z1).  This means that v1 in file 1 which is v100 in file 2.  A map!

Let's say we have a third file which has a different shape but is structured the same as file 2 - a morph.  The same vert index to vert index map that applies to file 1 and 2 also allies to file 1 and 3.  We can use this to map backwards to set file 1 verts (or a copy) to the values of file 3's verts.


If we want to change the original file, we set all the verts in file 1 to values in file 3, looking up which vert in 1 shoulld be changed for each vert in 3.  EG:see that v100 in file 3 is v1 in file 1.  So set v1(x,y,z) = to v100(x,y,z)

If file 1 was a source OBJ for a Poser Figure, then the final file may be used as a geometry file for a Poser full Body Morph for that figure.  It's vert indices will be the same as the source OBJ.

![flow](https://user-images.githubusercontent.com/1562991/190336870-fdcaab3a-ebe3-45ce-890a-0716f31eaebc.png)
