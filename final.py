# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from pxr import Usd,UsdGeom,Gf,Sdf
import numpy as np
from sklearn.cluster import KMeans
import re
sublayer_num=3
kmeans_num=3
kmeans_axis=[0,1,2]
hire_num=1
stage = Usd.Stage.Open('D:/usd/three/GameObject.usd')

s=stage.GetRootLayer().ExportToString()
# find prims that has transform which should be considered in subdivide
prims=[x for x in stage.Traverse() if x.HasProperty('xformOp:transform')]
otherprims=[x for x in stage.Traverse() if not x.HasProperty('xformOp:transform')]

transforms=[]
trs=[]
scales=[]
# calculate the world pos of the prims
for x in prims:
    splits = str(x.GetPath()).split('/')
    newpath = ''
    co = 1
    for index, splitsiter in enumerate(splits):
        if index == 0:
            continue
        newpath = newpath + '/' + splitsiter
        prim = stage.GetPrimAtPath(newpath)
        co = prim.GetAttribute('xformOp:transform').Get() * co
    trs.append(co)
    transforms.append(co[3])
    scales.append((co[0][0],co[1][1],co[2][2]))



poss=[]

for i in range(len(transforms)):
    tmp=[]
    for num in kmeans_axis:
        tmp.append(transforms[i][num])
    poss.append(tmp)
array=np.array(poss)
kmeans = KMeans(n_clusters=sublayer_num, random_state=0).fit(array)
print(kmeans.labels_)
stage2 = Usd.Stage.CreateNew('kmeans.usda')
# write no transform prims into the main stage file such as shader info
for prim in otherprims:
    nprim=stage2.DefinePrim(prim.GetPath(),prim.GetPrimTypeInfo().GetTypeName())
    attrs = prim.GetAuthoredAttributes()
    for att in attrs:
        if att.Get() is None:
            natt=nprim.CreateAttribute(att.GetName(), att.GetTypeName())
            if att.GetConnections() is not None:
                natt.SetConnections(att.GetConnections())
        else:
            natt=nprim.CreateAttribute(att.GetName(), att.GetTypeName())
            natt.Set(att.Get())
            if att.GetConnections() is not None:
                natt.SetConnections(att.GetConnections())
sublayers=[]
sdfpaths=[]
strs=[]
sinds=[]
for i in range(sublayer_num):
    strs.append([])
    sinds.append([])
for i in range(len(trs)):
    sdfpaths.append('/xform' + str(kmeans.labels_[i]))
    sinds[kmeans.labels_[i]].append(i)
    strs[kmeans.labels_[i]].append(poss[i])
def bvhconstruct(iter_num,ttrs,tinds):
    if iter_num==0:
        return
    array = np.array(ttrs)
    kmeans = KMeans(n_clusters=kmeans_num, random_state=0).fit(array)
    ntrs=[]
    ninds=[]
    for i in range(kmeans_num):
        ntrs.append([])
        ninds.append([])
    for i in range(len(tinds)):
        idx=tinds[i]
        sdfpaths[idx]=sdfpaths[idx]+'/hire'+str(kmeans.labels_[i])
        ntrs[kmeans.labels_[i]].append(poss[idx])
        ninds[kmeans.labels_[i]].append(idx)
    for i in range(kmeans_num):
        bvhconstruct(iter_num-1,ntrs[i],ninds[i])
for i in range(sublayer_num):
    bvhconstruct(hire_num, strs[i], sinds[i])
for i in range(sublayer_num):
    sublayers.append(Usd.Stage.CreateNew('sublayer'+str(i)+'.usda'))
for i in range(len(trs)):
    attrs=prims[i].GetAuthoredAttributes()
    # curpath=prims[i].GetPrimPath()
    # splits=curpath.split('/')
    # for splitsiter in splits:

    mesh = sublayers[kmeans.labels_[i]].DefinePrim(sdfpaths[i] +'/mesh' + str(i), 'Mesh')
    # cube.CreateAttribute('xformOp:transform', Sdf.ValueTypeNames.Matrix4d).Set(trs[i])
    # cube.GetAttribute("xformOpOrder").Set(["xformOp:transform"])
    rels=prims[i].GetAuthoredRelationships()
    for att in attrs:
        if att.Get() is None:
            mesh.CreateAttribute(att.GetName(), att.GetTypeName())
        else:
            mesh.CreateAttribute(att.GetName(), att.GetTypeName()).Set(att.Get())
    for rel in rels:
        mesh.CreateRelationship(rel.GetName(),False).SetTargets(rel.GetTargets())

    mesh.GetAttribute('xformOp:transform').Set(trs[i])

# save sublayers
for i in range(sublayer_num):
    sublayers[i].GetRootLayer().Save()
    stage2.GetRootLayer().subLayerPaths.append('sublayer'+str(i)+'.usda')
stage2.GetRootLayer().Save()

