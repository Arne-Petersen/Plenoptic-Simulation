import math

from . import data

# dot product for 2d vectors
def dot(v, w):
    return v[0]*w[0]+v[1]*w[1]

# calculates signed angle between two 2d vectors
def angle(v, w):
    signed_angle = math.atan2(w[1], w[0]) - math.atan2(v[1], v[0])
    if signed_angle > math.pi:
        signed_angle = signed_angle - 2.0 * math.pi
    if signed_angle < -math.pi:
        signed_angle = signed_angle + 2.0 * math.pi
    return signed_angle

# calculates the intersection of a ray and a lens surface
def calculate_new_position(ray, lens):
    # get lens surface data
    center = lens['position']
    radius = lens['radius']
    flip = (radius < 0.0)
    if flip:
        radius = - radius
    height = lens['semi_aperture']

    # ray hitting a spherical surface
    if radius > 0.0:
        # calculate intersection of surface and ray
        p_c = [ray[0] - center, ray[1]]
        v = [math.cos(ray[2]), math.sin(ray[2])]

        pc = dot(p_c,p_c)
        pcv = dot(p_c,v)
        squared = radius * radius - pc + pcv * pcv
        if squared < 0.0:
            return [0.0,0.0,180.0]

        lambd = 0.0
        if flip:
            lambd = - pcv + math.sqrt(squared)
        else:
            lambd = - pcv - math.sqrt(squared)

        intersection = [ray[0] + lambd * v[0], ray[1] + lambd * v[1]]
        
        if lambd < 0.0 or math.fabs(intersection[1]) > height:
            return [0.0,0.0,180.0]
        
        return [intersection[0], intersection[1], ray[2]]

    # ray hitting a flat surface
    if radius == 0.0:
        return [center, ray[1] + math.tan(ray[2]) * (center - ray[0]), ray[2]]

# calculate new ray direction based on Snell's law
def calculate_new_direction(ray, lens):
    # get lens surface data
    ior = lens['ior_ratio']
    normal = [lens['position']-ray[0],-ray[1]]
    if lens['radius'] < 0.0:
        normal = [-normal[0], -normal[1]]
    if lens['radius'] == 0.0:
        normal = [1.0, 0.0]

    direction = [math.cos(ray[2]), math.sin(ray[2])]
    incident_angle = angle(normal, direction)
    
    # apply Snell's law
    sin_of_angle = ior * math.sin(math.fabs(incident_angle))
    if math.fabs(sin_of_angle) > 1.0: #reflection instead of transmission
        return [0,0,180.0]

    new_angle = math.copysign(math.asin(sin_of_angle), incident_angle)

    normal_angle = angle([1.0, 0.0],normal)

    #print("Normal "+str(normal[0])+" / "+str(normal[1])+" Direction "+str(direction[0])+" / "+str(direction[1]))
    #print("Input angle "+str(ray[2]/math.pi*180.0)+" Output angle "+str((new_angle+normal_angle)/math.pi*180.0)+" Normal angle "+str(normal_angle/math.pi*180.0))
    #print("Incident "+str(incident_angle/math.pi*180.0)+" IOR "+str(ior)+" Outgoing "+str(new_angle/math.pi*180.0))
    #print("Position "+str(ray[0])+" / "+str(ray[1])+" Lens position "+str(lens['position']))

    return [ray[0], ray[1], new_angle + normal_angle]

# trace ray through one surface - returns a ray with angle 180.0 if tracing fails
def trace_step(ray, lens):
    new_pos_ray = calculate_new_position(ray, lens)
    if new_pos_ray[2] == 180.0:
        return new_pos_ray
    else:
        traced_ray = calculate_new_direction(new_pos_ray, lens)
        return traced_ray

# check if ray passes through aperture
def check_aperture(ray):
    # calculate intersection of ray and aperture plane
    intersection = ray[1] - ray[0]*math.tan(ray[2])
    # rays close to the aperture are ignored to take into account the non-circle aperture shape 
    return (math.fabs(intersection) < 0.9*data.semi_aperture) 

# trace a ray through all lens surfaces - returns -1.0 if tracing fails
def trace_single_ray(ray):
    #print("")
    #print("New Ray!")
    new_ray = ray

    if data.aperture_index == -1:
        if not check_aperture(ray):
            return [0,0,180.0]

    for i in range(0, len(data.objective)):
        if i != data.aperture_index:
            new_ray = trace_step(ray, data.objective[i])
            ray = new_ray
            if ray[2] == 180.0:
                break
        else: # check if ray passes through aperture
            if not check_aperture(ray):
                ray = [0,0,180.0]
                break
    
    return ray


# calculate the optimal sensor position for the given set of rays 
def calculate_sensor_pos(rays):
    if len(rays) == 0:
        return -1

    zeroes = []
    for ray in rays:
        b = ray[1]-ray[0]*math.tan(ray[2])
        m = math.tan(ray[2])
        if m != 0:
            zeroes.append(-b/m)
    
    circle_position = 0.0
    for zero in zeroes:
        circle_position = circle_position + zero

    return circle_position/float(len(zeroes))

# calculate the optimal sensor position for focusing on the desired distance - returns -1.0 if tracing fails
def sensor_position_for_distance(distance):

    # check if objective loaded
    if len(data.objective) == 0:
        print("No objective has been loaded.")
        return -1

    # set ray starting position
    position = [-distance, 0.0]

    # calculate maximum ray angle with respect to the x-axis
    max_direction = [data.objective[0]['position'] - data.objective[0]['radius'] + distance, data.objective[0]['semi_aperture']]
    max_angle = angle([1,0], max_direction)

    # trace rays starting from desired distance
    collected_rays = []
    current_angle = max_angle
    best_angle = 0
    for i in range(1, 10):
        traced_ray = trace_single_ray([position[0], position[1], current_angle])
        if traced_ray[2] != 180.0:
            best_angle = current_angle
            current_angle = current_angle + (1.0/math.pow(2.0, i))*max_angle
            if current_angle > max_angle:
                break
        else:
            current_angle = current_angle - (1.0/math.pow(2.0, i))*max_angle

    for i in range(1, 41):
        resulting_ray = trace_single_ray([position[0], position[1], float(i)/40.0 * best_angle])
        
        if resulting_ray[2] != 180.0:
            collected_rays.append(resulting_ray)

    return calculate_sensor_pos(collected_rays)