import numpy as np

from gensim.models import Word2Vec
from numba import njit
from .base import UnsupervisedModel


class Deepwalk(UnsupervisedModel):
    """
        Implementation of DeepWalk Unsupervised Graph Neural Networks (DeepWalk). 
        [DeepWalk: Online Learning of Social Representations](https://arxiv.org/abs/1403.6652)
        Implementation: https://github.com/phanein/deepwalk

        Arguments:
        ----------
            adj: `scipy.sparse.csr_matrix` (or `csc_matrix`) with shape (N, N)
                The input `symmetric` adjacency matrix, where `N` is the number of nodes 
                in graph.
            features: `np.array` with shape (N, F)
                The input node feature matrix, where `F` is the dimension of node features.
            labels: `np.array` with shape (N,)
                The ground-truth labels for all nodes in graph.
            device (String, optional): 
                The device where the model is running on. You can specified `CPU` or `GPU` 
                for the model. (default: :obj: `CPU:0`, i.e., the model is running on 
                the 0-th device `CPU`)
            seed (Positive integer, optional): 
                Used in combination with `tf.random.set_seed & np.random.seed & random.seed` 
                to create a reproducible sequence of tensors across multiple calls. 
                (default :obj: `None`, i.e., using random seed)
            name (String, optional): 
                Name for the model. (default: name of class)

    """    

    def __init__(self, adj, features, labels, device='CPU:0', seed=None, **kwargs):

        super().__init__(adj, features, labels, device=device, seed=seed, **kwargs)


    def build(self, walk_length=80, walks_per_node=10, 
              embedding_dim=64, window_size=5, workers=16, 
              iter=1, num_neg_samples=1):
        
        walks = self.deepwalk_random_walk(self.adj.indices, 
                                     self.adj.indptr,
                                     walk_length=walk_length,
                                     walks_per_node=walks_per_node)
        

        sentences = [list(map(str, walk)) for walk in walks]
        
        model = Word2Vec(sentences, size=embedding_dim, window=window_size, min_count=0, sg=1, workers=workers,
                     iter=iter, negative=num_neg_samples, hs=0, compute_loss=True)
        self.model = model
        
    @staticmethod
    @njit
    def deepwalk_random_walk(indices, indptr, walk_length=80, walks_per_node=10):

        N = len(indptr) - 1

        for _ in range(walks_per_node):
            for n in range(N):
                single_walk = [n]
                current_node = n
                for _ in range(walk_length-1):
                    neighbors = indices[indptr[current_node]:indptr[current_node + 1]]
                    if neighbors.size == 0: break
                    current_node = np.random.choice(neighbors)
                    single_walk.append(current_node)

                yield single_walk
                
    def get_embeddings(self, norm=True):
        embeddings = self.model.wv.vectors[np.fromiter(map(int, self.model.wv.index2word), np.int32).argsort()]

        if norm:
            embeddings = self._normalize_embedding(embeddings)

        self.embeddings = embeddings
