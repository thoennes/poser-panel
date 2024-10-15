# poser-panel
A Blender Add-on to help working with Poser exported OBJ files in Blender

## Summary
Using 2 OBJ files of the same *exact* mesh shape but with different vert orders and/or counts, creates a map that can be used to transfer shapes between a second pair with the same vert orders and face structures as the first pair.

## Reason for this Add-on
I wanted to use Blender for sculpting Poser Figure morphs.  Blender's sculpting tools have come a long way and provide a full mesh sculpting and editing suite of tools.  But Poser's OBJ export is not optimal for sculpting in Blender.  If the mesh is exported from Poser as a unimesh (ie: "welded"), which is best for sculpting, the resulting mesh can't be used used as a morph in Poser because Poser exports the OBJ with a different ordering of the vertexes.  If the mesh is exported unwelded, while Poser can use that as a morph since the vertex order matches Poser's internal order, the mesh is actually a group of disconnected sub-meshes that tear apart when sculpting across submeshes.  Some 3D programs have an ability to "weld" the vertexes so they act as a single mesh (as Poser does).  But this is unusual.  And, more importantly, Blender does not.

What's needed is a mesh that's the same as the original OBJ (vert order, etc.) *but* with the shape of Poser's internal Object.

## Explanation

Poser, like all 3d applications, creates an internal Object representation of the original OBJ.

![arm area of figure](./arm.png) "Arm area of a Figure's mesh"

Different than many more recent 3D applications, Poser structures a multi-actor Object (eg: a Figure) as a group of disconnected submeshes, one for each actor.

Note: It's more common, now, to use a "unimesh" with weight maps to move the vertexes according to the rig.  But Poser predates that method and it's quite involved and expensive to change as nealy everything within the application depends on the original method.

![forearm submesh of figure](./forearm.png) "Forearm sub-mesh of the Arm"

For each actor that joins to another actor, the common mesh edge is shared; that is, the vertexes that make up the shared edge are duplicated in each submesh and logically "welded" by Poser.  During figure creation, when Poser splits the original unimesh, those shared vertexes are doubled.  Once for each sub-mesh.

![forearm shared edges](./forearm-edge.png) "Forearm edges shared with other sub-meshes (in this case, Hand and Shoulder)"

What's needed is a way to get a Poser exported Object, in OBJ format back into the same structure as the original OBJ.  That is, *impose* a shaped Poser Object in OBJ format on an original OBJ.  Essentially, we need a mapping between original OBJ vertex indexes and Poser OBJ vcertex indexes.

## Problem Analysis
During Figure creation, Poser splits the source OBJ unimesh into sub-meshes which are used internally.

Poser loses the original OBJ structure during this process.  Poser does not maintain a record of the original vertex indexes and how they map to Posers vertexes.

The result of this is that Poser cannot export an OBJ in the same vertex order as the original OBJ.  Without the "weld" option, the export OBJ will not even have the same vertex count, as the Poser "splitting" process duplicated vertexes of the shared edges.  Even using the "weld" OBJ export option, this only "unimeshes" the mesh; the vert order is still different than the original OBJ.

Because of this, the Poser exported OBj cannot be used (practically) in other programs as a mesh to produce shapes that are then used to morph the source Poser figure.

A caveat: Poser *can* actually use the exported and split OBJ as a source mesh for its own morphs.  However, such a split mesh cannot be easily sculpted in external applications (like Blender) since, during sculpting, the mesh seams "pull apart".

Also, a Poser exported OBJ cannot be used to transfer a shape (ie: morph) to the same Figure in Daz Dtudio (DS).

We need two things to fix this:
- A mapping from original vertex indexes to Poser vertex indexes.
- A way to use that info to create an original vertex ordered OBJ *but* with the shape of the Poser vert ordered OBJ.

# Description of Solution
This Add-on uses some of the characteristics of Poser export, OBJs, and Blender import to counter this problem.

1. Poser exports a zero'd mesh with the vertices all in the same exact position as the source OBJ but in a different order.  You don't even need the same number of verts. You do need the polygroups (ie: Actors) and it's also handy to have the material groups, which helps with complex selections in Blender.
2. Blender imports an OBJ maintaining the source order, UVs, and mats. It imports OBJ polygroups as Blender vertex groups.
3. Blender saves an OBJ with vertexes in the same order as its internal Object.  For Objects that came from an OBJ import, the vertexes are written in the same order as the imported OBJ

So, if we have a source OBJ, and a Poser exported OBJ with unchanged vertexes, we can compare them and find a mapping between one vert order and the other.

This add-on uses Python dictionaries and lists to do do.  In some languages, dictionaries are known as associative arrays.  In Python, dicts can be keyed using tuples.  A Tuple is a list of numbers seaprated by commas.  As in the X,Y,Z of a vertex.

If we have an original OBJ and a Poser OBJ (that is zero'd and came from that original OBJ), then a dict keyed on each vertex X,Y,Z with be the same!  That is, for every vertex(x,y,z) of the first OBJ, there will be exactly one vertex(x,y,z) of the second OBJ *and* vice versa.

In short, the list of keys from one OBJ will be equal to the list of keys for the second OBJ.

So what do we store in the dictionaries?  The indexes of the vertex that has that key.

# Example

3 meshes, in 2D with simple x and y's to keep it brief, clear, and simple.  We'll be using the indexes, directly, to represent the vertex positions.  In reality, the vertexes are actually a class that has (x,y,z) positions.  Those positions are used to make INT based (X,Y,Z) dictionaries of the Vertex indexes.

- Mesh 1 and Mesh 2 are the same shape BUT different vert order and number of points.
- Mesh 2 and 3 are the same vert order and number of points BUT different shapes

We will use all this to make the first mesh look like the third mesh.  How we would use this, in reality, is to make a Poser exported OBJ with morph(s) into a shaped version of the original OBJ, suitable for using directly as a morph in DS or Poser, or sculpting in Blender then exporting and an OBJ suitabkle for use as a morph in either


mesh 1: 

2x2 face unimesh, 9 verts

1. 0,0
2. 1,0
3. 2,0
4. 0,1
5. 1,1
6. 2,1
7. 0,2
8. 1,2
9. 2,2

mesh 2: a split version of the same mesh; ie: same shape, different verts (into 2 1x2 meshes, with a shared edge up the middle)
1. 0,0
2. 1,0
3. 1,0
4. 2,0
5. 0,1
6. 1,1
7. 1,1
8. 2,1
9. 0,2
10. 1,2
11. 1,2
12. 2,2

A dictionary of the first mesh, key=x,y value=index list (ie: indexes with this key)
- mesh1(0,0) = [1]
- mesh1(1,0) = [2]
- mesh1(2,0) = [3]
- mesh1(0,1) = [4]
- mesh1(1,1) = [5]
- mesh1(2,1) = [6]
- mesh1(0,2) = [7]
- mesh1(1,2) = [8]
- mesh1(2,2) = [9]

A dictionary of the first mesh, key=x,y value=index list (ie: indexes with this key)
- mesh2(0,0) = [1]
- mesh2(1,0) = [2,3]
- mesh2(2,0) = [4]
- mesh2(0,1) = [5]
- mesh2(1,1) = [6,7]
- mesh2(2,1) = [8]
- mesh2(0,2) = [9]
- mesh2(1,2) = [10,11]
- mesh2(2,2) = [12]

This gives us the map we need!  Starting with a mesh 2 vertex or index 7, we get the key of (1,1).  Then we look at Mesh1(1,1) and get it's index of 5.  Index 7 (and index 6, since those vertexes are "welded") in the second mesh corresponds to index 5 of the first mesh.

Nice.

Now, if we have a third mesh that has the same vert order as that second mesh (that is index1 of the first = index1 of the second, etc.) We can use that map to impose the shape of the third mesh ON the first mesh, mapping *through* mesh 2 (reemember: the Poser exported ZERO version of the orignal)

mesh 3: a mesh with the same vert order as the second, BUT with different shape.  In this case, shifted by 1 in x and 2 in y

1. 1,2
2. 2,2
3. 2,2
4. 3,2
5. 1,3
6. 2,3
7. 2,3
8. 3,3
9. 1,4
10. 2,4
11. 2,4
12. 3,4

Resulting dict
- mesh2(1,2) = [1]
- mesh2(2,2) = [2,3]
- mesh2(3,2) = [4]
- mesh2(1,3) = [5]
- mesh2(2,3) = [6,7]
- mesh2(3,3) = [8]
- mesh2(1,4) = [9]
- mesh2(2,4) = [10,11]
- mesh2(3,4) = [12]

Now, to make the first mesh have the same shape as this.

For each vert in the third mesh, we get it's key.  That's it's (x,y).  We'll want to move the correct index in Mesh 1 to that (x,y).  So we find the key for this third index in the second mesh (it's the same index).  Then use *that* key in the first mesh to find the index of the vertex.  We set the vert at that index to the same (x,y) as the third mesh.

Index 1 of third mesh.  Gives us an (x,y) of (1,2).  In mesh2, that same index has a key of (0,0).  Mesh1(0,0) gives us an index of 1.  
So we set index 1 to the (x,y) of mesh 3.  Repeating for each vertex, we get a Mesh 4 that looks like.


1. 1,2
2. 2,2
3. 3,2
4. 1,3
5. 2,3
6. 3,3
7. 1,4
8. 2,4
9. 3,4

This is an OBJ with the same structure as mesh1, but with the shape of mesh 3.  This mesh could be used as a FBM in Poser or DS for a figure that was made from Mesh 1.  It could also be changed in Blender without splitting.  Then exported as an OBJ and used in Poser or DS.

Cool.



![flow](https://user-images.githubusercontent.com/1562991/190336870-fdcaab3a-ebe3-45ce-890a-0716f31eaebc.png)
