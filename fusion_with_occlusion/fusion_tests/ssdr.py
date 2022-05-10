import os
import sys
import time
from . import pyssdr
import numpy as np 
from scipy import sparse
from sklearn.cluster import KMeans

class SSDR(pyssdr.MyDemBones):
    def __init__(self):
        super().__init__()
        self.removed_bones_list = []

    def load_anime_file(self,filename):
        f = open(filename, 'rb')
        nf = np.fromfile(f, dtype=np.int32, count=1)[0]
        nv = np.fromfile(f, dtype=np.int32, count=1)[0]
        nt = np.fromfile(f, dtype=np.int32, count=1)[0]
        vert_data = np.fromfile(f, dtype=np.float32, count=nv * 3)
        face_data = np.fromfile(f, dtype=np.int32, count=nt * 3)
        offset_data = np.fromfile(f, dtype=np.float32, count=-1)
        vert_data = vert_data.reshape((-1, 3))
        face_data = face_data.reshape((-1, 3))
        offset_data = offset_data.reshape((nf - 1, nv, 3))

        trajectory = np.tile(vert_data.reshape((1,-1,3)),(nf,1,1))
        trajectory[1:] += offset_data

        return trajectory,face_data

    def check_sparse_matrix(self,skinning_anchors,skinning_weights):
        # w = sparse.load_npz(os.path.join(savepath,f"weights_{0}.npz"))
        w = self.w
        w_dense = self.w.todense()
        print(w.indices.shape,w.indptr.shape,w.data.shape,w.shape,w.nnz)
        for col in range(w.shape[1]): # Loop over all the cols
            anchors = skinning_anchors[col]
            for nz_id in range(w.indptr[col],w.indptr[col+1]): # Loop over all ids for that row
                row = w.indices[nz_id]
                val = w.data[nz_id]

                anchor = np.where(anchors==row)[0]
                assert len(anchor) == 1,f"W(skinning vector is wrong), For {col}, graph node:{row} not present in {anchors}"         
                anchor = anchor[0]
                assert val == skinning_weights[col,anchor], f"W[{row,col}] = {val} != {skinning_weights[col,anchor]}"

        return True


    def get_transforms(self,trajectory,faces,skinning_anchors,skinning_weights,graph_nodes):


        # Preprocess trajectory to pass as input
        U = trajectory[0]
        trajectory = trajectory.transpose((0,2,1))
        T,D,N = trajectory.shape
        trajectory = trajectory.reshape((D*T,N))

        # Set parameters to initize SSDR
        self.nInitIters = 10
        self.tolerance = 1e-2
        self.bindUpdate=2
        self.nIters = 5
        self.global_update_threshold = np.inf
        self.min_bones = 1
        self.patience = 1

        self.load_data(trajectory,faces)
        self.nB = len(graph_nodes)

        # Use skinning weights to set values of a sparse matrix

        row = []
        col = []
        data = []
        for v,anchors in enumerate(skinning_anchors):
            for b,a in enumerate(anchors):
                if a != -1:
                    row.append(a)
                    col.append(v)
                    data.append(skinning_weights[v,b])

        self.w = sparse.csc_matrix((data,(row,col)),shape=(self.nB,N))   
        self.m = np.tile(np.eye(4,4),(T,self.nB))
        # self.check_sparse_matrix(skinning_anchors,skinning_weights)
        print(self.w.shape)
        print(self.m.shape)

        self.lockW = np.ones(self.nV,dtype=self.lockW.dtype)
        self.lockM = np.zeros(self.nB,dtype=self.lockM.dtype)
        self.keep_bones = np.array(range(self.nB))

        self.computeTranformations()


        return self.m,self.rmse()            
