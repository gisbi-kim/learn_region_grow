import h5py
import sys
import numpy
import matplotlib.pyplot as plt
from class_util import classes

def loadFromH5(filename):
	f = h5py.File(filename,'r')
	all_points = f['points'][:]
	count_room = f['count_room'][:]
	tmp_points = []
	idp = 0
	for i in range(len(count_room)):
		tmp_points.append(all_points[idp:idp+count_room[i], :])
		idp += count_room[i]
	f.close()
	room = []
	obj_labels = []
	class_labels = []
	for i in range(len(tmp_points)):
		room.append(tmp_points[i][:,:-2])
		obj_labels.append(tmp_points[i][:,-2].astype(int))
		class_labels.append(tmp_points[i][:,-1].astype(int))
	return room, obj_labels, class_labels

def savePLY(filename, points):
	f = open(filename,'w')
	f.write("""ply
format ascii 1.0
element vertex %d
property float x
property float y
property float z
property uchar r
property uchar g
property uchar b
end_header
""" % len(points))
	for p in points:
		f.write("%f %f %f %d %d %d\n"%(p[0],p[1],p[2],p[3],p[4],p[5]))
	f.close()
	print('Saved to %s: (%d points)'%(filename, len(points)))

numRooms = 0
combined_points = []
all_room_id = None
resolution = 0.1

mode = 'rgb'
if '--rgb' in sys.argv:
	mode = 'rgb'
if '--seg' in sys.argv:
	mode = 'seg'

all_points, all_obj_id, all_cls_id = loadFromH5(sys.argv[1])

for room_id in range(len(all_points)):
	unequalized_points = all_points[room_id]
	obj_id = all_obj_id[room_id]
	cls_id = all_cls_id[room_id]

	#equalize resolution
	equalized_idx = []
	unequalized_idx = []
	equalized_map = {}
	for i in range(len(unequalized_points)):
		k = tuple(numpy.round(unequalized_points[i,:3]/resolution).astype(int))
		if not k in equalized_map:
			equalized_map[k] = len(equalized_idx)
			equalized_idx.append(i)
		unequalized_idx.append(equalized_map[k])
	points = unequalized_points[equalized_idx] #(N,6)
	obj_id = obj_id[equalized_idx]
	cls_id = cls_id[equalized_idx]

	if mode=='rgb':
		points[:,3:6] = (points[:,3:6]+0.5)*255
		savePLY('data/rgb/%d.ply'%room_id, points)
	elif mode=='seg':
		if numpy.min(obj_id)==0:
			obj_id += 1
		color_sample_state = numpy.random.RandomState(0)
		obj_color = color_sample_state.randint(0,255,(numpy.max(obj_id)+1,3))
		unique_id, count = numpy.unique(obj_id, return_counts=True)
		reorder_id = numpy.zeros(len(obj_id), dtype=int)
		for k in range(len(unique_id)):
			i = unique_id[numpy.argsort(count)][::-1][k]
			target_class = classes[cls_id[numpy.nonzero(obj_id==i)[0][0]]]
			if target_class!='ceiling':
				plt.scatter(0,0,color=tuple(obj_color[k+1]/255.0),label='%s #%d'%(target_class, k),s=200)
			reorder_id[obj_id==i] = k+1
		plt.legend(ncol=min(7,(k+1)/2),prop={'size': 16},loc='lower left')
#		plt.show()
		obj_color[0,:] = [200,200,200]
		unequalized_points[:,3:6] = obj_color[reorder_id,:][unequalized_idx]
		savePLY('data/gt/%d.ply'%room_id, unequalized_points)
