def median(values):
    ordered = sorted(values)
    n = len(ordered)
    if n % 2 == 0:
        return (ordered[n // 2 - 1] + ordered[n // 2]) / 2
    else:
        return ordered[n // 2]
