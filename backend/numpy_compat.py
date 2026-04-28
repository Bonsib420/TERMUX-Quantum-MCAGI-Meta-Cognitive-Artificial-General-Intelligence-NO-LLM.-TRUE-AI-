"""
Numpy compatibility wrapper for Termux.
Falls back to pure Python if numpy is not available.
"""

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    
    class NumpyFallback:
        """Pure Python numpy replacement for basic operations."""
        
        @staticmethod
        def array(x):
            if isinstance(x, list):
                return x
            return list(x)
        
        @staticmethod
        def zeros(shape):
            if isinstance(shape, int):
                return [0.0] * shape
            if isinstance(shape, tuple):
                if len(shape) == 1:
                    return [0.0] * shape[0]
                return [[0.0] * shape[1] for _ in range(shape[0])]
            return [0.0]
        
        @staticmethod
        def ones(shape):
            if isinstance(shape, int):
                return [1.0] * shape
            if isinstance(shape, tuple):
                if len(shape) == 1:
                    return [1.0] * shape[0]
                return [[1.0] * shape[1] for _ in range(shape[0])]
            return [1.0]
        
        @staticmethod
        def mean(x, axis=None):
            if isinstance(x, (list, tuple)):
                flat = []
                for item in x:
                    if isinstance(item, (list, tuple)):
                        flat.extend(item)
                    else:
                        flat.append(item)
                return sum(flat) / len(flat) if flat else 0
            return x
        
        @staticmethod
        def sum(x, axis=None):
            if isinstance(x, (list, tuple)):
                flat = []
                for item in x:
                    if isinstance(item, (list, tuple)):
                        flat.extend(item)
                    else:
                        flat.append(item)
                return sum(flat)
            return x
        
        @staticmethod
        def dot(a, b):
            if isinstance(a[0], (list, tuple)):
                # Matrix-vector or matrix-matrix
                result = []
                for row in a:
                    if isinstance(b[0], (list, tuple)):
                        result.append([sum(x * y for x, y in zip(row, col)) for col in zip(*b)])
                    else:
                        result.append(sum(x * y for x, y in zip(row, b)))
                return result
            return sum(x * y for x, y in zip(a, b))
        
        @staticmethod
        def sqrt(x):
            import math
            if isinstance(x, (list, tuple)):
                return [math.sqrt(i) if i >= 0 else 0 for i in x]
            return math.sqrt(x) if x >= 0 else 0
        
        @staticmethod
        def exp(x):
            import math
            if isinstance(x, (list, tuple)):
                return [math.exp(min(i, 700)) for i in x]  # Prevent overflow
            return math.exp(min(x, 700))
        
        @staticmethod
        def log(x):
            import math
            if isinstance(x, (list, tuple)):
                return [math.log(max(i, 1e-10)) for i in x]
            return math.log(max(x, 1e-10))
        
        @staticmethod
        def max(x, axis=None):
            if isinstance(x, (list, tuple)):
                flat = []
                for item in x:
                    if isinstance(item, (list, tuple)):
                        flat.extend(item)
                    else:
                        flat.append(item)
                return max(flat) if flat else 0
            return x
        
        @staticmethod
        def argmax(x, axis=None):
            if isinstance(x, (list, tuple)):
                return x.index(max(x))
            return 0
        
        @staticmethod
        def clip(x, a_min, a_max):
            if isinstance(x, (list, tuple)):
                return [max(a_min, min(a_max, i)) for i in x]
            return max(a_min, min(a_max, x))
        
        @staticmethod
        def abs(x):
            if isinstance(x, (list, tuple)):
                return [abs(i) for i in x]
            return abs(x)
        
        class random:
            @staticmethod
            def random():
                import random
                return random.random()
            
            @staticmethod
            def randint(low, high=None, size=None):
                import random
                if high is None:
                    high = low
                    low = 0
                if size is None:
                    return random.randint(low, high - 1)
                return [random.randint(low, high - 1) for _ in range(size)]
            
            @staticmethod
            def choice(a, size=None, replace=True, p=None):
                import random
                if size is None:
                    if p:
                        return random.choices(a, weights=p, k=1)[0]
                    return random.choice(a)
                if p:
                    return random.choices(a, weights=p, k=size)
                if replace:
                    return [random.choice(a) for _ in range(size)]
                return random.sample(a, min(size, len(a)))
            
            @staticmethod
            def uniform(low=0.0, high=1.0, size=None):
                import random
                if size is None:
                    return random.uniform(low, high)
                return [random.uniform(low, high) for _ in range(size)]
        
        float64 = float
        float32 = float
        int64 = int
        int32 = int
        
        @staticmethod
        def asarray(x):
            return list(x) if not isinstance(x, list) else x
    
    np = NumpyFallback()


def get_numpy():
    """Get numpy or fallback."""
    return np


def has_numpy():
    """Check if real numpy is available."""
    return HAS_NUMPY
