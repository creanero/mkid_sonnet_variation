



class mkid(object):
    def __init__(self):
        self.__resonator = resonator()

    pass


class polygon(object):
    def __init__(self, polygon_id=100):
        self.__x_coords = []
        self.__y_coords = []
        self.__polygon_id = polygon_id
    def add_point(self, x, y):
        self.__x_coords.append(x)
        self.__y_coords.append(y)
    def clear_points(self):
        self.__x_coords = []
        self.__y_coords = []
    def get_points(self):
        return self.__x_coords, self.__y_coords
    def get_num_points(self):
        return len(self.__x_coords)
    def gen_sonnet_polygon(self):
        # Generate the polygon in the Sonnet format
        out_text = "0 5 0 N {} 1 1 100 100 0 0 0 Y".format(self.__polygon_id)
        # iterate through the points and add them to the output text
        for x, y in zip(self.__x_coords, self.__y_coords):
            # Add each point to the output text on a new line
            out_text += "\n{} {}".format(x, y)
        # Close the polygon by returning to the first point
        out_text += "\n{} {}".format(self.__x_coords[0], self.__y_coords[0]) 
        return out_text


class rectangle(polygon):
    def set_min_max(self, x_min, x_max, y_min, y_max):
        if x_min >= x_max or y_min >= y_max:
            raise ValueError("Invalid rectangle coordinates: x_min must be less than x_max and y_min must be less than y_max.")
        elif len(self.__x_coords) > 0 or len(self.__y_coords) > 0:
            raise ValueError("Rectangle points have already been set. Clear the points before setting new ones.")
        else:
            # Add the points to the polygon
            self.add_point(x_min, y_min)
            self.add_point(x_max, y_min)
            self.add_point(x_max, y_max)
            self.add_point(x_min, y_max)
    def set_start_height_breadth(self, x_start, y_start, height, breadth):
        if height <= 0 or breadth <= 0:
            raise ValueError("Height and breadth must be positive values.")
        elif len(self.__x_coords) > 0 or len(self.__y_coords) > 0:
            raise ValueError("Rectangle points have already been set. Clear the points before setting new ones.")
        else:
            # Add the points to the polygon
            self.add_point(x_start, y_start)
            self.add_point(x_start + breadth, y_start)
            self.add_point(x_start + breadth, y_start + height)
            self.add_point(x_start, y_start + height)


class geometry_element(object):
    def __init__(self):
        self.__polygons = []
    
    def get_polygons(self):
        return self.__polygons
    def get_polygons_string(self):
        out_string = ""
        for polygon in self.get_polygons():
            out_string += "\n{}".format(polygon.gen_sonnet_polygon())
        return out_string

class capacitor(geometry_element):
    def __init__(self):
        super().__init__()
        self.__fingers = fingers()
        self.__frame = frame()

    def get_polygons(self):
        polygons = []
        polygons = polygons.append(self.__fingers.get_polygons())
        polygons = polygons.append(self.__frame.get_polygons())
        return polygons   


class frame(geometry_element):
    def __init__(self):
        super().__init__()
        # These are the edges of the capacitor.
        cap_left_out = 0.0
        cap_left_in = cap_left_out + cap_side_breadth
        cap_right_out = args.x_size - ground_plane_sidebar_breadth - cap_side_space
        cap_right_in = cap_right_out - cap_side_breadth
        cap_vert_space = 4.0
        cap_top_breadth = 10.0
        cap_top_out = resonator_top + cap_vert_space + inductor_height
        cap_top_in = cap_top_out + cap_top_breadth
        transfer_bar_breadth = 5.0
        transfer_bar_end = 250.0
        transfer_bar_out = resonator_bottom - cap_vert_space
        transfer_bar_in = transfer_bar_out - transfer_bar_breadth

class fingers(geometry_element):
    def __init__(self):
        super().__init__()
        # initialize the capacitor parameters to default values
        self.__num_fingers = 27
        self.__finger_breadth = 2.0
        self.__finger_length = 450.0
        self.__finger_space = 2.0
        self.__finger_pitch = self.__finger_breadth + self.__finger_space
        self.__finger_final_length = 84.0
        self.__polygons = []
        self.gen_fingers()


    def gen_fingers(self):
        # generate the polygons for the fingers of the capacitor
        for i in range(self.__num_fingers):
            # create a new rectangle for each finger
            finger = rectangle()
            # set the start position and dimensions of the finger
            # TODO: import this from the old version of the code
            # add the finger to the list of polygons
            self.__polygons.append(finger)



class inductor(geometry_element):
    def __init__(self):
        self.__num_turns = 5
        self.__width = 20.0
        self.__turn_breadth = 1.0
        self.__turn_space = 1.0
        self.__turn_pitch = self.__turn_breadth + self.__turn_space
        self.__turn_length = self.__width - 2 * (self.__turn_pitch)


class resonator(object):
    def __init__(self):
        self.__bottom = 0.0
        self.__top = 0.0
        self.__left = 0.0
        self.__right = 0.0
        self.__inductor = inductor()
        self.__capacitor = capacitor()

    

