class MultiDimIterator:
    def __init__(self, sizes):
        """
        sizes: dict with keys 'F', 'D', 'U', 'S', 'M', 'C', 'E', 'T' and their respective bin counts (integers >=1)
        Assumes flattening order: F (outermost) to T (innermost), row-major style.
        """
        self.params = ["F", "D", "U", "S", "M", "C", "E", "T"]
        self.sizes = {p: sizes[p] for p in self.params}
        self.strides = self._compute_strides()

    def _compute_strides(self):
        strides = {}
        stride = 1
        for p in reversed(self.params):  # Start from innermost
            strides[p] = stride
            stride *= self.sizes[p]
        return strides

    def get_iterator(self, free_param, fixed_values):
        """
        free_param: str, one of the params like 'U'
        fixed_values: dict with {param: int} for all params except free_param, values within 0 to sizes[param]-1
        Returns a generator yielding flat indices (offsets) as it iterates over the free_param.
        """
        if free_param not in self.params:
            raise ValueError("Invalid free parameter")
        missing = set(self.params) - set(fixed_values.keys()) - {free_param}
        if missing:
            raise ValueError(f"Missing fixed values for: {missing}")
        extra = set(fixed_values.keys()) - set(self.params)
        if extra:
            raise ValueError(f"Extra fixed values for: {extra}")

        # Validate fixed values
        for p, v in fixed_values.items():
            if not (0 <= v < self.sizes[p]):
                raise ValueError(f"Invalid value {v} for {p}, must be 0-{self.sizes[p]-1}")

        # Compute base offset from fixed params
        base = 0
        for p, v in fixed_values.items():
            base += v * self.strides[p]

        free_size = self.sizes[free_param]
        free_stride = self.strides[free_param]

        def generator():
            for i in range(free_size):
                yield base + i * free_stride

        return generator()


# Example usage:
# sizes = {'F': 1, 'D': 2, 'U': 3, 'S': 1, 'M': 4, 'C': 1, 'E': 1, 'T': 5}
# it = MultiDimIterator(sizes)
# for idx in it.get_iterator('U', {'F': 0, 'D': 1, 'S': 0, 'M': 2, 'C': 0, 'E': 0, 'T': 3}):
#     print(idx)
