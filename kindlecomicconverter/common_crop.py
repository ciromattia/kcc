def threshold_from_power(power):
    return 240-(power*64)


'''
Groups close values together
'''
def group_close_values(vals, max_dist_tolerated):
    groups = []

    group_start = -1
    group_end = 0
    for i in range(len(vals)):
        dist = vals[i] - group_end
        if group_start == -1:
            group_start = vals[i]
            group_end = vals[i]
        elif dist <= max_dist_tolerated:
            group_end = vals[i]
        else:
            groups.append((group_start, group_end))
            group_start = -1
            group_end = -1
            
    if group_start != -1:
        groups.append((group_start, group_end))
        
    return groups
