import itertools
from collections import OrderedDict


class MultiDimIterator:
    def __init__(self, sizes):
        """
        sizes: dict with keys 'F', 'D', 'U', 'S', 'M', 'C', 'E', 'T' and bin counts (>=1)
        Flattening order: F (outermost) -> T (innermost)
        """
        self.params = ["F", "D", "U", "S", "M", "C", "E", "T"]
        self.sizes = {p: sizes[p] for p in self.params}
        self.strides = self._compute_strides()

    def _compute_strides(self):
        strides = {}
        stride = 1
        for p in reversed(self.params):
            strides[p] = stride
            stride *= self.sizes[p]
        return strides

    def _validate_inputs(self, free_params, fixed_values):
        if isinstance(free_params, str):
            free_params = [free_params]

        free_set = set(free_params)
        if not free_set.issubset(self.params):
            invalid = free_set - set(self.params)
            raise ValueError(f"Invalid free parameters: {invalid}")

        fixed_set = set(fixed_values.keys())
        if free_set & fixed_set:
            raise ValueError(f"Parameters cannot be both free and fixed: {free_set & fixed_set}")

        missing = set(self.params) - free_set - fixed_set
        if missing:
            raise ValueError(f"Missing fixed values for parameters: {missing}")

        for p, v in fixed_values.items():
            if not (0 <= v < self.sizes[p]):
                raise ValueError(
                    f"Invalid fixed value {v} for '{p}' (must be 0 to {self.sizes[p]-1})"
                )

        return free_params  # return as-is (do NOT sort)

    def iter_indices(self, free_params, fixed_values):
        """Yield flat indices in the order of free_params (first in list = slowest varying)"""
        free_params = self._validate_inputs(free_params, fixed_values)

        base = sum(v * self.strides[p] for p, v in fixed_values.items())

        # Use free_params in the order provided by user
        free_ranges = [range(self.sizes[p]) for p in free_params]
        free_strides = [self.strides[p] for p in free_params]

        for combo in itertools.product(*free_ranges):
            offset = base + sum(i * s for i, s in zip(combo, free_strides))
            yield offset

    def iter_coords(self, free_params, fixed_values, format="dict"):
        """
        Yield full coordinates.
        format: "dict" (OrderedDict in original param order), "tuple", or "free_only"
        """
        free_params = self._validate_inputs(free_params, fixed_values)

        full_coord = fixed_values.copy()
        free_ranges = [range(self.sizes[p]) for p in free_params]

        for combo in itertools.product(*free_ranges):
            for p, val in zip(free_params, combo):
                full_coord[p] = val

            if format == "dict":
                yield OrderedDict(
                    (p, full_coord.get(p, 0)) for p in self.params
                )  # 0 for size-1 params if missing
            elif format == "tuple":
                yield tuple(full_coord.get(p, 0) for p in self.params)
            elif format == "free_only":
                yield dict(zip(free_params, combo))  # or tuple(combo) if you prefer
            else:
                raise ValueError("format must be 'dict', 'tuple', or 'free_only'")

    def iter_items(self, free_params, fixed_values, coord_format="dict"):
        """Yield (coords, flat_index) pairs"""
        coord_gen = self.iter_coords(free_params, fixed_values, format=coord_format)
        index_gen = self.iter_indices(free_params, fixed_values)
        for coord, idx in zip(coord_gen, index_gen):
            yield coord, idx


if __name__ == "__main__":
    # Example: Control the order explicitly
    sizes = {"F": 2, "D": 1, "U": 3, "S": 1, "M": 4, "C": 1, "E": 2, "T": 5}
    it = MultiDimIterator(sizes)

    fixed = {"F": 0, "D": 0, "S": 0, "C": 0}

    # You want T to vary fastest, then U, then M (M slowest)
    free_params = ["M", "U", "T"]  # <-- your desired order

    print("Iteration order (M slowest, then U, then T fastest):")
    for coord, idx in it.iter_items(free_params, fixed):
        m, u, t = coord["M"], coord["U"], coord["T"]
        print(f"M={m}, U={u}, T={t}  →  flat index: {idx}")
